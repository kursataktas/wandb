// Code generated by smithy-go-codegen DO NOT EDIT.

package types

import (
	"fmt"
	smithy "github.com/aws/smithy-go"
)

// The requested bucket name is not available. The bucket namespace is shared by
// all users of the system. Select a different name and try again.
type BucketAlreadyExists struct {
	Message *string

	ErrorCodeOverride *string

	noSmithyDocumentSerde
}

func (e *BucketAlreadyExists) Error() string {
	return fmt.Sprintf("%s: %s", e.ErrorCode(), e.ErrorMessage())
}
func (e *BucketAlreadyExists) ErrorMessage() string {
	if e.Message == nil {
		return ""
	}
	return *e.Message
}
func (e *BucketAlreadyExists) ErrorCode() string {
	if e == nil || e.ErrorCodeOverride == nil {
		return "BucketAlreadyExists"
	}
	return *e.ErrorCodeOverride
}
func (e *BucketAlreadyExists) ErrorFault() smithy.ErrorFault { return smithy.FaultClient }

// The bucket you tried to create already exists, and you own it. Amazon S3
// returns this error in all Amazon Web Services Regions except in the North
// Virginia Region. For legacy compatibility, if you re-create an existing bucket
// that you already own in the North Virginia Region, Amazon S3 returns 200 OK and
// resets the bucket access control lists (ACLs).
type BucketAlreadyOwnedByYou struct {
	Message *string

	ErrorCodeOverride *string

	noSmithyDocumentSerde
}

func (e *BucketAlreadyOwnedByYou) Error() string {
	return fmt.Sprintf("%s: %s", e.ErrorCode(), e.ErrorMessage())
}
func (e *BucketAlreadyOwnedByYou) ErrorMessage() string {
	if e.Message == nil {
		return ""
	}
	return *e.Message
}
func (e *BucketAlreadyOwnedByYou) ErrorCode() string {
	if e == nil || e.ErrorCodeOverride == nil {
		return "BucketAlreadyOwnedByYou"
	}
	return *e.ErrorCodeOverride
}
func (e *BucketAlreadyOwnedByYou) ErrorFault() smithy.ErrorFault { return smithy.FaultClient }

// Object is archived and inaccessible until restored.
//
// If the object you are retrieving is stored in the S3 Glacier Flexible Retrieval
// storage class, the S3 Glacier Deep Archive storage class, the S3
// Intelligent-Tiering Archive Access tier, or the S3 Intelligent-Tiering Deep
// Archive Access tier, before you can retrieve the object you must first restore a
// copy using [RestoreObject]. Otherwise, this operation returns an InvalidObjectState error. For
// information about restoring archived objects, see [Restoring Archived Objects]in the Amazon S3 User Guide.
//
// [RestoreObject]: https://docs.aws.amazon.com/AmazonS3/latest/API/API_RestoreObject.html
// [Restoring Archived Objects]: https://docs.aws.amazon.com/AmazonS3/latest/dev/restoring-objects.html
type InvalidObjectState struct {
	Message *string

	ErrorCodeOverride *string

	StorageClass StorageClass
	AccessTier   IntelligentTieringAccessTier

	noSmithyDocumentSerde
}

func (e *InvalidObjectState) Error() string {
	return fmt.Sprintf("%s: %s", e.ErrorCode(), e.ErrorMessage())
}
func (e *InvalidObjectState) ErrorMessage() string {
	if e.Message == nil {
		return ""
	}
	return *e.Message
}
func (e *InvalidObjectState) ErrorCode() string {
	if e == nil || e.ErrorCodeOverride == nil {
		return "InvalidObjectState"
	}
	return *e.ErrorCodeOverride
}
func (e *InvalidObjectState) ErrorFault() smithy.ErrorFault { return smithy.FaultClient }

// The specified bucket does not exist.
type NoSuchBucket struct {
	Message *string

	ErrorCodeOverride *string

	noSmithyDocumentSerde
}

func (e *NoSuchBucket) Error() string {
	return fmt.Sprintf("%s: %s", e.ErrorCode(), e.ErrorMessage())
}
func (e *NoSuchBucket) ErrorMessage() string {
	if e.Message == nil {
		return ""
	}
	return *e.Message
}
func (e *NoSuchBucket) ErrorCode() string {
	if e == nil || e.ErrorCodeOverride == nil {
		return "NoSuchBucket"
	}
	return *e.ErrorCodeOverride
}
func (e *NoSuchBucket) ErrorFault() smithy.ErrorFault { return smithy.FaultClient }

// The specified key does not exist.
type NoSuchKey struct {
	Message *string

	ErrorCodeOverride *string

	noSmithyDocumentSerde
}

func (e *NoSuchKey) Error() string {
	return fmt.Sprintf("%s: %s", e.ErrorCode(), e.ErrorMessage())
}
func (e *NoSuchKey) ErrorMessage() string {
	if e.Message == nil {
		return ""
	}
	return *e.Message
}
func (e *NoSuchKey) ErrorCode() string {
	if e == nil || e.ErrorCodeOverride == nil {
		return "NoSuchKey"
	}
	return *e.ErrorCodeOverride
}
func (e *NoSuchKey) ErrorFault() smithy.ErrorFault { return smithy.FaultClient }

// The specified multipart upload does not exist.
type NoSuchUpload struct {
	Message *string

	ErrorCodeOverride *string

	noSmithyDocumentSerde
}

func (e *NoSuchUpload) Error() string {
	return fmt.Sprintf("%s: %s", e.ErrorCode(), e.ErrorMessage())
}
func (e *NoSuchUpload) ErrorMessage() string {
	if e.Message == nil {
		return ""
	}
	return *e.Message
}
func (e *NoSuchUpload) ErrorCode() string {
	if e == nil || e.ErrorCodeOverride == nil {
		return "NoSuchUpload"
	}
	return *e.ErrorCodeOverride
}
func (e *NoSuchUpload) ErrorFault() smithy.ErrorFault { return smithy.FaultClient }

// The specified content does not exist.
type NotFound struct {
	Message *string

	ErrorCodeOverride *string

	noSmithyDocumentSerde
}

func (e *NotFound) Error() string {
	return fmt.Sprintf("%s: %s", e.ErrorCode(), e.ErrorMessage())
}
func (e *NotFound) ErrorMessage() string {
	if e.Message == nil {
		return ""
	}
	return *e.Message
}
func (e *NotFound) ErrorCode() string {
	if e == nil || e.ErrorCodeOverride == nil {
		return "NotFound"
	}
	return *e.ErrorCodeOverride
}
func (e *NotFound) ErrorFault() smithy.ErrorFault { return smithy.FaultClient }

// This action is not allowed against this storage tier.
type ObjectAlreadyInActiveTierError struct {
	Message *string

	ErrorCodeOverride *string

	noSmithyDocumentSerde
}

func (e *ObjectAlreadyInActiveTierError) Error() string {
	return fmt.Sprintf("%s: %s", e.ErrorCode(), e.ErrorMessage())
}
func (e *ObjectAlreadyInActiveTierError) ErrorMessage() string {
	if e.Message == nil {
		return ""
	}
	return *e.Message
}
func (e *ObjectAlreadyInActiveTierError) ErrorCode() string {
	if e == nil || e.ErrorCodeOverride == nil {
		return "ObjectAlreadyInActiveTierError"
	}
	return *e.ErrorCodeOverride
}
func (e *ObjectAlreadyInActiveTierError) ErrorFault() smithy.ErrorFault { return smithy.FaultClient }

// The source object of the COPY action is not in the active tier and is only
// stored in Amazon S3 Glacier.
type ObjectNotInActiveTierError struct {
	Message *string

	ErrorCodeOverride *string

	noSmithyDocumentSerde
}

func (e *ObjectNotInActiveTierError) Error() string {
	return fmt.Sprintf("%s: %s", e.ErrorCode(), e.ErrorMessage())
}
func (e *ObjectNotInActiveTierError) ErrorMessage() string {
	if e.Message == nil {
		return ""
	}
	return *e.Message
}
func (e *ObjectNotInActiveTierError) ErrorCode() string {
	if e == nil || e.ErrorCodeOverride == nil {
		return "ObjectNotInActiveTierError"
	}
	return *e.ErrorCodeOverride
}
func (e *ObjectNotInActiveTierError) ErrorFault() smithy.ErrorFault { return smithy.FaultClient }
