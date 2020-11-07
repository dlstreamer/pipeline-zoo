'''
* Copyright (C) 2019-2020 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''
import abc
import yaml
import json
import jsonschema
from jsonschema import Draft7Validator, validators, RefResolver
from types import SimpleNamespace
import os
import functools
from collections import OrderedDict

def extend_with_default(validator_class):
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        for property, subschema in properties.items():
            if "default" in subschema:
                instance.setdefault(property, subschema["default"])
                
            if "type" in subschema and subschema["type"]=="integer":
                try:
                    instance[property] = int(instance[property])
                except:
                    pass
            if "type" in subschema and subschema["type"]=="number":
                try:
                    instance[property] = float(instance[property])
                except:
                    pass

        for error in validate_properties(
            validator, properties, instance, schema,
        ):
            yield error

    return validators.extend(
        validator_class, {"properties" : set_defaults},
    )

DefaultValidatingDraft7Validator = extend_with_default(Draft7Validator)

def _add_schema_to_store(schema, store):
    if isinstance(schema,dict):
        if '$id' in schema:
            store[schema['$id']] = schema
        for key,value in schema.items():
            _add_schema_to_store(value,store)
    if isinstance(schema,list):
        for value in schema:
            _add_schema_to_store(value,store)

def _load_document(document_path):
    document = None
    with open(document_path) as document_file:
        if (document_path.endswith('.yml')):
            document = yaml.full_load(document_file)
        elif (document_path.endswith('.json')):
            document = json.load(document_file)
    return document

def _task_name_from_path(task_path):
    return os.path.basename(task_path).replace('.task.yml','').replace('.task.json','')
    
def load_schemas(args):
    schema_directory = os.path.join(args.zoo_root,"tools/pipebench/pipebench/schema")
    
    args.schemas = load_schema_store([schema_directory])
    return args.schemas


def load_tasks(args):
    tasks = {}
    tasks_directory = os.path.join(args.zoo_root,"pipelines")
    for root,dirs,files in os.walk(tasks_directory):
        for path in files:
            if path.endswith('.task.yml') or path.endswith('.task.json'):
                try:
                    task = TaskConfig(os.path.join(root,path),args)
                    tasks[task.name] = task
                except Exception as error:
                    print("Ignoring Invalid task: {}".format(os.path.join(root,path)))
                
                    
    args.tasks = tasks
    return tasks


def load_schema_store(directories):
    store = {}
    for directory in directories:
        schema_paths = [os.path.join(directory,path) for path in os.listdir(directory)
                        if path.endswith('.schema.yml') or path.endswith('.schema.json')]

        for schema_path in schema_paths:
            try:
                schema = _load_document(schema_path)
                Draft7Validator.check_schema(schema)
                _add_schema_to_store(schema,store)
            except Exception as error:
                print("Ignoring invalid schema: {} error: {}".format(schema_path,error))
                
    return store

def rsetdict(obj, attr, val):
    pre, _, post = attr.rpartition('.')
    dictionary = rgetdict(obj, pre, {}) if pre else obj
    dictionary[post] = val
    return dictionary
    
def rgetdict(obj,attr,*args):
    def _getdict(obj, attr):
        return obj.setdefault(attr, {})
    return functools.reduce(_getdict, [obj] + attr.split('.'))

def rsetattr(obj, attr, val):
    pre, _, post = attr.rpartition('.')
    return setattr(rgetattr(obj, pre) if pre else obj, post, val)

def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return functools.reduce(_getattr, [obj] + attr.split('.'))

def convert_to_namespace(value):
    if isinstance(value,dict):
        value = SimpleNamespace(**value)
        for key,item in vars(value).items():
            if (isinstance(item,dict)):
                setattr(value,key,convert_to_namespace(item))
            if (isinstance(item,list)):
                new_list = []
                for list_item in item:
                    new_list.append(convert_to_namespace(list_item))
                setattr(value,key,new_list)
    return value

def _is_instance_schema(document, schema, schema_store):
    resolver = RefResolver("","",schema_store)
    try:
        DefaultValidatingDraft7Validator(schema,resolver=resolver).validate(document)
    except:
        return False
    return True


def apply_overrides(document,overrides = []):
    if (overrides):
        for key,value in overrides:
            temp = None
            try:
                temp = yaml.full_load(value)
                temp = {} if temp is None else temp
            except Exception as error:
                pass
                
            if (temp is not None):
                value = temp
            rsetdict(document,key,value)

def validate(document_path, schema_store, overrides = [] ):

    root, extension = os.path.splitext(document_path)
    root, schema = os.path.splitext(root)
    if not schema:
        schema = os.path.basename(root)
    schema_id = schema.strip('.')
    resolver = RefResolver("","",schema_store)
    document = None
    
    try:
        document = _load_document(document_path)
        apply_overrides(document,overrides)
        if (schema_id and schema_id in schema_store):
            schema = schema_store[schema_id]
            DefaultValidatingDraft7Validator(schema,resolver=resolver).validate(document)
    except Exception as error:
        print("Error validating: {} error: {}".format(document_path,error))
        document = None
    return document

class Document(object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def __init__(self, filepath, schema_store):
        pass


class TaskConfig(Document):
    def __init__(self, document_path, args):

        self._document = validate(document_path,args.schemas)

        self._namespace = convert_to_namespace(self._document)


        self.name = None

        if (_is_instance_schema(self._document, args.schemas['operator'], args.schemas)):
            self.name = _task_name_from_path(document_path)
        elif (_is_instance_schema(self._document,args.schemas['scenario-list'],args.schemas)):
            self.name = _task_name_from_path(document_path)
        else:
            self.name = list(self._document.keys())[0]
            self._document = self._document[self.name]


        self._scenarios = {}

        if (isinstance(self._document,list)):
            for scenario in self._document:
                namespace = convert_to_namespace(scenario)
                self._scenarios[frozenset(namespace.scenario.__dict__.items())] = namespace.pipeline
            self._scenarios['default'] = list(self._scenarios.items())[0][1]
        else:
            self._scenarios['default'] = self._document

    def get_task_scenario(self,scenario):
        if (isinstance(scenario,dict)):
            key = frozenset(scenario.items())
        elif (isinstance(scenario,SimpleNamespace)):
            key = frozenset(scenario.__dict__.items())

        if key in self._scenarios:
            return self._scenarios[key]
        else:
            return self._scenarios['default']
        
                
class PipelineConfig(Document):
    def __init__(self, document_path, args):
        self._document = validate(document_path,args.schemas)

        self._namespace = convert_to_namespace(self._document)

        self._task = args.tasks[self._namespace.task]

        self.pipeline_root = os.path.dirname(document_path)
        self.pipeline_path = document_path


        
        
class WorkloadConfig(Document):

    def _find_default_media(self, args):

        media_list_path = os.path.join(args.pipeline_root,"media.list.yml")
        document = validate(media_list_path,args.schemas)
        if (document) and isinstance(document,list):
            return document[0]
        else:
            extensions = [".mp4"]
            media_root = os.path.join(args.pipeline_root,"media")            
            for root,dirs,paths in os.walk(media_root):

                file_paths = [os.path.relpath(root,media_root)
                              for path in paths if os.path.splitext(path)[1] in extensions]
                if (file_paths):
                    return file_paths[0]
    
    def __init__(self, document_path, args):

        
        self._document = validate(document_path,args.schemas,args.overrides)

        if (not self._document):
            raise Exception("Invalid Workload {}".format(document_path))
        self._namespace = convert_to_namespace(self._document)
        if (not "media" in self._document):
            self._document["media"] = self._find_default_media(args)
            self._namespace.media = self._document["media"]
            
        self.media = self._namespace.media
        
        self.pipeline = args.pipeline

        
        
        
