# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: wandb/proto/wandb_base.proto
# Protobuf Python Version: 5.26.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1cwandb/proto/wandb_base.proto\x12\x0ewandb_internal\"6\n\x0b_RecordInfo\x12\x11\n\tstream_id\x18\x01 \x01(\t\x12\x14\n\x0c_tracelog_id\x18\x64 \x01(\t\"!\n\x0c_RequestInfo\x12\x11\n\tstream_id\x18\x01 \x01(\t\"#\n\x0b_ResultInfo\x12\x14\n\x0c_tracelog_id\x18\x64 \x01(\tB\x1bZ\x19\x63ore/pkg/service_go_protob\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'wandb.proto.wandb_base_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  _globals['DESCRIPTOR']._loaded_options = None
  _globals['DESCRIPTOR']._serialized_options = b'Z\031core/pkg/service_go_proto'
  _globals['__RECORDINFO']._serialized_start=48
  _globals['__RECORDINFO']._serialized_end=102
  _globals['__REQUESTINFO']._serialized_start=104
  _globals['__REQUESTINFO']._serialized_end=137
  _globals['__RESULTINFO']._serialized_start=139
  _globals['__RESULTINFO']._serialized_end=174
# @@protoc_insertion_point(module_scope)
