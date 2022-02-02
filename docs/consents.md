# Consents

## Updating Contents

Since each new consent modification implies the creation of new blocks in the user's blockchain, publishing them is
only a matter of posting consents' metadata to the relevant API endpoint. There are two supported methods according
to the contents being pushed, which will be described in following subsections.

Note that ``data`` contents itself, whether provided as plain string in JSON body or with multipart contents, will not 
be stored directly in the blockchain. This is done to preserve private data separately from public consents metadata. 
Posted metadata in other fields of ``subsystems`` entries should also refrain from supplying sensitive data. If such 
data should be linked, it should be encrypted using as many [Encoded-Data Consents](#encoded-data-consents) parts 
as required.

### Metadata-Only Consents

When only changes to metadata about a consent is required, such as revoking a consent, extending its duration with a
new expiration date, or simply pushing a consent that does not specifically require encoded data, a simple JSON request 
body can be used.

```http request
POST /chains/{{chain_id}}/consents
Host: localhost:5000
Content-Type: application/json

{
    "action": "first-name-read",
    "consent": true,
    "expire": null
}
```

Note that ``subsystems`` field (more detail in [Encoded-Data Consents](#encoded-data-consents)) can also be specified 
although only metadata is being provided in this case. In this situation, the ``data`` field within the ``subsystems``
item should be explicitly provided as ``null``. 

Note that plain string ``data`` could also be provided instead of ``null`` if desired, but this value should be 
insensitive data following proper anonymization to avoid data privacy issues, since it cannot be revoked nor hidden
once persisted in the blockchain. 
Most other ``subsystems`` fields are optional and left to the consents' publisher to provide more metadata to better
represent the referenced item as necessary. For example, ``metadata`` field can contain any mapping which could 
provide additional information required by the publisher to retrieve referenced contents from a remote platform. 

```http request
POST /chains/{{chain_id}}/consents
Host: localhost:5000
Content-Type: application/json

{
    "action": "share-data",
    "consent": true,
    "expire": "2050-01-01T08:00:00",
    "subsystems": [
        {
            "data": null,
            "data_type": "message",
            "data_provider": "Best Social Media Plaform",
            "data_source": "https://best.social.media.com",
            "data_description": "user post",            
            "media_type": "text/plain",
            "medatada": {
                "message-id": "123456"
            }
        }
    ]
}
```

### Encoded-Data Consents

When some data is needed to be supplied to better represent consents being defined, but that such data is more 
appropriately defined using an encoded representation rather than plain strings, multipart contents can be used instead.

Providing the original data to establish a relationship with the added consents allows to automatically generate an 
encrypted representation of that data within the block. This guarantees that any defined consents cannot be 
misinterpreted (purposely or not) against mismatching data sources, since the data-consents association can be validated
at a later point using the original data for comparison.

When supplying content in parts as shown below, the first part of the body should be a similar JSON definition to 
the one presented in [Metadata-Only Consents](#metadata-only-consents), but adding the relevant metadata details 
in ``subsystems`` field to represent that new data defined in other parts. Explicit ``Content-ID: meta`` should 
be indicated as well in this part to identify it as the metadata definition of ``subsystems`` applied to the consents.

All ``subsystems`` entries should define their corresponding ``data_id`` field using the specified ``Content-ID`` from
other parts. This will provide the necessary details for the application to map relevant elements together. Naturally, 
there should be at least as many subsequent parts as there are ``subsystems`` entries with an associated ``data_id``.
If any part entry (except the JSON metadata) cannot be mapped between its ``data_id`` and one ``Content-ID``, the 
request will fail to avoid corrupted or incomplete consent definitions.

Some fields like ``media_type`` and ``data_description`` can be omitted from their respective ``subsystems`` if they 
are provided through ``Content-Type`` and ``Content-Description`` headers of their part. 
Furthermore, other ``subsystems`` entries can still be provided literally in the JSON definition as described in the
[Metadata-Only Consents](#metadata-only-consents) section, but using ``data`` rather than ``data_id`` in this case.
Those additional definitions don't require to have any associated multipart content.

```http request
POST /chains/{{chain_id}}/consents
Host: localhost:5000
Content-Type: multipart/related; boundary="simple boundary"

--simple boundary
Content-Type: application/json; charset=UTF-8
Content-ID: meta

{
    "action": "share-data",
    "consent": true,
    "expire": "2050-01-01T08:00:00",
    "subsystems": [
        {
            "data_id": "<PROFILE-IMAGE>",
            "data_type": "image",
            "data_provider": "Best Social Media Plaform",
            "data_source": "https://best.social.media.com"
        }
    ]
}

--simple boundary
Content-Type: image/png; base64
Content-Description: profile image
Content-ID: <PROFILE-IMAGE>

iVBORw0KGgoAAAANSUhEUgAAAZAAAAGQCAYAAAC...

--simple boundary--
```

**WARNING**

As per [RFC-7578 section 4.1](https://datatracker.ietf.org/doc/html/rfc7578#section-4.1), parts MUST be separated by
``CRLF`` instead of ``LF``. In the above example, all *empty lines* (i.e.: following each ``Content-ID`` and before 
each boundary in this case), should therefore be represented as double ``CRLF`` entries in the request body.
