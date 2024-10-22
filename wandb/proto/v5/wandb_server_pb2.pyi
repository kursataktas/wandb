"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""

import builtins
import google.protobuf.descriptor
import google.protobuf.message
import typing
import wandb.proto.wandb_base_pb2
import wandb.proto.wandb_internal_pb2
import wandb.proto.wandb_settings_pb2

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class ServerAuthenticateRequest(google.protobuf.message.Message):
    """Authentication messages.

    These messages are used to authenticate the client with the W&B server.
    The client sends a ServerAuthenticateRequest message to wandb-core, which
    verifies the API key on the server specified by the base_url field and
    returns a ServerAuthenticateResponse message with the default entity and
    error status.
    """

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    API_KEY_FIELD_NUMBER: builtins.int
    BASE_URL_FIELD_NUMBER: builtins.int
    _INFO_FIELD_NUMBER: builtins.int
    api_key: builtins.str
    base_url: builtins.str
    @property
    def _info(self) -> wandb.proto.wandb_base_pb2._RecordInfo: ...
    def __init__(
        self,
        *,
        api_key: builtins.str = ...,
        base_url: builtins.str = ...,
        _info: wandb.proto.wandb_base_pb2._RecordInfo | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["_info", b"_info"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["_info", b"_info", "api_key", b"api_key", "base_url", b"base_url"]) -> None: ...

global___ServerAuthenticateRequest = ServerAuthenticateRequest

@typing.final
class ServerAuthenticateResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    DEFAULT_ENTITY_FIELD_NUMBER: builtins.int
    ERROR_STATUS_FIELD_NUMBER: builtins.int
    _INFO_FIELD_NUMBER: builtins.int
    default_entity: builtins.str
    error_status: builtins.str
    @property
    def _info(self) -> wandb.proto.wandb_base_pb2._RecordInfo: ...
    def __init__(
        self,
        *,
        default_entity: builtins.str = ...,
        error_status: builtins.str = ...,
        _info: wandb.proto.wandb_base_pb2._RecordInfo | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["_info", b"_info"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["_info", b"_info", "default_entity", b"default_entity", "error_status", b"error_status"]) -> None: ...

global___ServerAuthenticateResponse = ServerAuthenticateResponse

@typing.final
class ServerShutdownRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    _INFO_FIELD_NUMBER: builtins.int
    @property
    def _info(self) -> wandb.proto.wandb_base_pb2._RecordInfo: ...
    def __init__(
        self,
        *,
        _info: wandb.proto.wandb_base_pb2._RecordInfo | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["_info", b"_info"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["_info", b"_info"]) -> None: ...

global___ServerShutdownRequest = ServerShutdownRequest

@typing.final
class ServerShutdownResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    def __init__(
        self,
    ) -> None: ...

global___ServerShutdownResponse = ServerShutdownResponse

@typing.final
class ServerStatusRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    _INFO_FIELD_NUMBER: builtins.int
    @property
    def _info(self) -> wandb.proto.wandb_base_pb2._RecordInfo: ...
    def __init__(
        self,
        *,
        _info: wandb.proto.wandb_base_pb2._RecordInfo | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["_info", b"_info"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["_info", b"_info"]) -> None: ...

global___ServerStatusRequest = ServerStatusRequest

@typing.final
class ServerStatusResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    def __init__(
        self,
    ) -> None: ...

global___ServerStatusResponse = ServerStatusResponse

@typing.final
class ServerInformInitRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    SETTINGS_FIELD_NUMBER: builtins.int
    _INFO_FIELD_NUMBER: builtins.int
    @property
    def settings(self) -> wandb.proto.wandb_settings_pb2.Settings: ...
    @property
    def _info(self) -> wandb.proto.wandb_base_pb2._RecordInfo: ...
    def __init__(
        self,
        *,
        settings: wandb.proto.wandb_settings_pb2.Settings | None = ...,
        _info: wandb.proto.wandb_base_pb2._RecordInfo | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["_info", b"_info", "settings", b"settings"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["_info", b"_info", "settings", b"settings"]) -> None: ...

global___ServerInformInitRequest = ServerInformInitRequest

@typing.final
class ServerInformInitResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    def __init__(
        self,
    ) -> None: ...

global___ServerInformInitResponse = ServerInformInitResponse

@typing.final
class ServerInformSyncRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    SETTINGS_FIELD_NUMBER: builtins.int
    _INFO_FIELD_NUMBER: builtins.int
    @property
    def settings(self) -> wandb.proto.wandb_settings_pb2.Settings: ...
    @property
    def _info(self) -> wandb.proto.wandb_base_pb2._RecordInfo: ...
    def __init__(
        self,
        *,
        settings: wandb.proto.wandb_settings_pb2.Settings | None = ...,
        _info: wandb.proto.wandb_base_pb2._RecordInfo | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["_info", b"_info", "settings", b"settings"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["_info", b"_info", "settings", b"settings"]) -> None: ...

global___ServerInformSyncRequest = ServerInformSyncRequest

@typing.final
class ServerInformSyncResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    _INFO_FIELD_NUMBER: builtins.int
    @property
    def _info(self) -> wandb.proto.wandb_base_pb2._RecordInfo: ...
    def __init__(
        self,
        *,
        _info: wandb.proto.wandb_base_pb2._RecordInfo | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["_info", b"_info"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["_info", b"_info"]) -> None: ...

global___ServerInformSyncResponse = ServerInformSyncResponse

@typing.final
class ServerInformStartRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    SETTINGS_FIELD_NUMBER: builtins.int
    _INFO_FIELD_NUMBER: builtins.int
    @property
    def settings(self) -> wandb.proto.wandb_settings_pb2.Settings: ...
    @property
    def _info(self) -> wandb.proto.wandb_base_pb2._RecordInfo: ...
    def __init__(
        self,
        *,
        settings: wandb.proto.wandb_settings_pb2.Settings | None = ...,
        _info: wandb.proto.wandb_base_pb2._RecordInfo | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["_info", b"_info", "settings", b"settings"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["_info", b"_info", "settings", b"settings"]) -> None: ...

global___ServerInformStartRequest = ServerInformStartRequest

@typing.final
class ServerInformStartResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    def __init__(
        self,
    ) -> None: ...

global___ServerInformStartResponse = ServerInformStartResponse

@typing.final
class ServerInformFinishRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    _INFO_FIELD_NUMBER: builtins.int
    @property
    def _info(self) -> wandb.proto.wandb_base_pb2._RecordInfo: ...
    def __init__(
        self,
        *,
        _info: wandb.proto.wandb_base_pb2._RecordInfo | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["_info", b"_info"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["_info", b"_info"]) -> None: ...

global___ServerInformFinishRequest = ServerInformFinishRequest

@typing.final
class ServerInformFinishResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    def __init__(
        self,
    ) -> None: ...

global___ServerInformFinishResponse = ServerInformFinishResponse

@typing.final
class ServerInformAttachRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    _INFO_FIELD_NUMBER: builtins.int
    @property
    def _info(self) -> wandb.proto.wandb_base_pb2._RecordInfo: ...
    def __init__(
        self,
        *,
        _info: wandb.proto.wandb_base_pb2._RecordInfo | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["_info", b"_info"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["_info", b"_info"]) -> None: ...

global___ServerInformAttachRequest = ServerInformAttachRequest

@typing.final
class ServerInformAttachResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    SETTINGS_FIELD_NUMBER: builtins.int
    _INFO_FIELD_NUMBER: builtins.int
    @property
    def settings(self) -> wandb.proto.wandb_settings_pb2.Settings: ...
    @property
    def _info(self) -> wandb.proto.wandb_base_pb2._RecordInfo: ...
    def __init__(
        self,
        *,
        settings: wandb.proto.wandb_settings_pb2.Settings | None = ...,
        _info: wandb.proto.wandb_base_pb2._RecordInfo | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["_info", b"_info", "settings", b"settings"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["_info", b"_info", "settings", b"settings"]) -> None: ...

global___ServerInformAttachResponse = ServerInformAttachResponse

@typing.final
class ServerInformDetachRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    _INFO_FIELD_NUMBER: builtins.int
    @property
    def _info(self) -> wandb.proto.wandb_base_pb2._RecordInfo: ...
    def __init__(
        self,
        *,
        _info: wandb.proto.wandb_base_pb2._RecordInfo | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["_info", b"_info"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["_info", b"_info"]) -> None: ...

global___ServerInformDetachRequest = ServerInformDetachRequest

@typing.final
class ServerInformDetachResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    def __init__(
        self,
    ) -> None: ...

global___ServerInformDetachResponse = ServerInformDetachResponse

@typing.final
class ServerInformTeardownRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    EXIT_CODE_FIELD_NUMBER: builtins.int
    _INFO_FIELD_NUMBER: builtins.int
    exit_code: builtins.int
    @property
    def _info(self) -> wandb.proto.wandb_base_pb2._RecordInfo: ...
    def __init__(
        self,
        *,
        exit_code: builtins.int = ...,
        _info: wandb.proto.wandb_base_pb2._RecordInfo | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["_info", b"_info"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["_info", b"_info", "exit_code", b"exit_code"]) -> None: ...

global___ServerInformTeardownRequest = ServerInformTeardownRequest

@typing.final
class ServerInformTeardownResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    def __init__(
        self,
    ) -> None: ...

global___ServerInformTeardownResponse = ServerInformTeardownResponse

@typing.final
class ServerRequest(google.protobuf.message.Message):
    """
    ServerRequest, ServerResponse: used in sock server
    """

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    RECORD_PUBLISH_FIELD_NUMBER: builtins.int
    RECORD_COMMUNICATE_FIELD_NUMBER: builtins.int
    INFORM_INIT_FIELD_NUMBER: builtins.int
    INFORM_FINISH_FIELD_NUMBER: builtins.int
    INFORM_ATTACH_FIELD_NUMBER: builtins.int
    INFORM_DETACH_FIELD_NUMBER: builtins.int
    INFORM_TEARDOWN_FIELD_NUMBER: builtins.int
    INFORM_START_FIELD_NUMBER: builtins.int
    AUTHENTICATE_FIELD_NUMBER: builtins.int
    INFORM_SYNC_FIELD_NUMBER: builtins.int
    @property
    def record_publish(self) -> wandb.proto.wandb_internal_pb2.Record: ...
    @property
    def record_communicate(self) -> wandb.proto.wandb_internal_pb2.Record: ...
    @property
    def inform_init(self) -> global___ServerInformInitRequest: ...
    @property
    def inform_finish(self) -> global___ServerInformFinishRequest: ...
    @property
    def inform_attach(self) -> global___ServerInformAttachRequest: ...
    @property
    def inform_detach(self) -> global___ServerInformDetachRequest: ...
    @property
    def inform_teardown(self) -> global___ServerInformTeardownRequest: ...
    @property
    def inform_start(self) -> global___ServerInformStartRequest: ...
    @property
    def authenticate(self) -> global___ServerAuthenticateRequest: ...
    @property
    def inform_sync(self) -> global___ServerInformSyncRequest: ...
    def __init__(
        self,
        *,
        record_publish: wandb.proto.wandb_internal_pb2.Record | None = ...,
        record_communicate: wandb.proto.wandb_internal_pb2.Record | None = ...,
        inform_init: global___ServerInformInitRequest | None = ...,
        inform_finish: global___ServerInformFinishRequest | None = ...,
        inform_attach: global___ServerInformAttachRequest | None = ...,
        inform_detach: global___ServerInformDetachRequest | None = ...,
        inform_teardown: global___ServerInformTeardownRequest | None = ...,
        inform_start: global___ServerInformStartRequest | None = ...,
        authenticate: global___ServerAuthenticateRequest | None = ...,
        inform_sync: global___ServerInformSyncRequest | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["authenticate", b"authenticate", "inform_attach", b"inform_attach", "inform_detach", b"inform_detach", "inform_finish", b"inform_finish", "inform_init", b"inform_init", "inform_start", b"inform_start", "inform_sync", b"inform_sync", "inform_teardown", b"inform_teardown", "record_communicate", b"record_communicate", "record_publish", b"record_publish", "server_request_type", b"server_request_type"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["authenticate", b"authenticate", "inform_attach", b"inform_attach", "inform_detach", b"inform_detach", "inform_finish", b"inform_finish", "inform_init", b"inform_init", "inform_start", b"inform_start", "inform_sync", b"inform_sync", "inform_teardown", b"inform_teardown", "record_communicate", b"record_communicate", "record_publish", b"record_publish", "server_request_type", b"server_request_type"]) -> None: ...
    def WhichOneof(self, oneof_group: typing.Literal["server_request_type", b"server_request_type"]) -> typing.Literal["record_publish", "record_communicate", "inform_init", "inform_finish", "inform_attach", "inform_detach", "inform_teardown", "inform_start", "authenticate", "inform_sync"] | None: ...

global___ServerRequest = ServerRequest

@typing.final
class ServerResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    RESULT_COMMUNICATE_FIELD_NUMBER: builtins.int
    INFORM_INIT_RESPONSE_FIELD_NUMBER: builtins.int
    INFORM_FINISH_RESPONSE_FIELD_NUMBER: builtins.int
    INFORM_ATTACH_RESPONSE_FIELD_NUMBER: builtins.int
    INFORM_DETACH_RESPONSE_FIELD_NUMBER: builtins.int
    INFORM_TEARDOWN_RESPONSE_FIELD_NUMBER: builtins.int
    INFORM_START_RESPONSE_FIELD_NUMBER: builtins.int
    AUTHENTICATE_RESPONSE_FIELD_NUMBER: builtins.int
    INFORM_SYNC_RESPONSE_FIELD_NUMBER: builtins.int
    @property
    def result_communicate(self) -> wandb.proto.wandb_internal_pb2.Result: ...
    @property
    def inform_init_response(self) -> global___ServerInformInitResponse: ...
    @property
    def inform_finish_response(self) -> global___ServerInformFinishResponse: ...
    @property
    def inform_attach_response(self) -> global___ServerInformAttachResponse: ...
    @property
    def inform_detach_response(self) -> global___ServerInformDetachResponse: ...
    @property
    def inform_teardown_response(self) -> global___ServerInformTeardownResponse: ...
    @property
    def inform_start_response(self) -> global___ServerInformStartResponse: ...
    @property
    def authenticate_response(self) -> global___ServerAuthenticateResponse: ...
    @property
    def inform_sync_response(self) -> global___ServerInformSyncResponse: ...
    def __init__(
        self,
        *,
        result_communicate: wandb.proto.wandb_internal_pb2.Result | None = ...,
        inform_init_response: global___ServerInformInitResponse | None = ...,
        inform_finish_response: global___ServerInformFinishResponse | None = ...,
        inform_attach_response: global___ServerInformAttachResponse | None = ...,
        inform_detach_response: global___ServerInformDetachResponse | None = ...,
        inform_teardown_response: global___ServerInformTeardownResponse | None = ...,
        inform_start_response: global___ServerInformStartResponse | None = ...,
        authenticate_response: global___ServerAuthenticateResponse | None = ...,
        inform_sync_response: global___ServerInformSyncResponse | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["authenticate_response", b"authenticate_response", "inform_attach_response", b"inform_attach_response", "inform_detach_response", b"inform_detach_response", "inform_finish_response", b"inform_finish_response", "inform_init_response", b"inform_init_response", "inform_start_response", b"inform_start_response", "inform_sync_response", b"inform_sync_response", "inform_teardown_response", b"inform_teardown_response", "result_communicate", b"result_communicate", "server_response_type", b"server_response_type"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["authenticate_response", b"authenticate_response", "inform_attach_response", b"inform_attach_response", "inform_detach_response", b"inform_detach_response", "inform_finish_response", b"inform_finish_response", "inform_init_response", b"inform_init_response", "inform_start_response", b"inform_start_response", "inform_sync_response", b"inform_sync_response", "inform_teardown_response", b"inform_teardown_response", "result_communicate", b"result_communicate", "server_response_type", b"server_response_type"]) -> None: ...
    def WhichOneof(self, oneof_group: typing.Literal["server_response_type", b"server_response_type"]) -> typing.Literal["result_communicate", "inform_init_response", "inform_finish_response", "inform_attach_response", "inform_detach_response", "inform_teardown_response", "inform_start_response", "authenticate_response", "inform_sync_response"] | None: ...

global___ServerResponse = ServerResponse
