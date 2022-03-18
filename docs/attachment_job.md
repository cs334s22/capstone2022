### Doc for Basic form of an Attachment Job

### Work Generator
The work generator will create jobs that contains the download URL in the relationships/attachements/links/related section of the comment JSON.

What a job looks like : 
{
    "job_id": 1234, 
    "url": url,
    "job_type": attachment,
}

These JSON's are received from the comments of MongoDB.
Jobs are then pushed to the job_waiting_queue in Redis.

### Work Server
Work server will send jobs over to the clients as a new endpoint for attachments.

### Client
Client will check the URL an determine if it is an attachment or not. This is done by adding 'attachements' to the end of the url.
If this is an attachment, it must download the list. Then returns the resulting JSON to server as a different PUT endpoint.

# Examples of returned JSON objects

### Example of an JSON without attachment endpoint.
https://api.regulations.gov/v4/comments/CMS-2022-0012-0392/?api_key=<API_KEY>
{
  "data" : {
    "id" : "CMS-2022-0012-0392",
    "type" : "comments",
    "links" : {
      "self" : "https://api.regulations.gov/v4/comments/CMS-2022-0012-0392"
    },
    "attributes" : {
      "commentOn" : "0900006484f1b7c3",
      "commentOnDocumentId" : "CMS-2022-0012-0001",
      "duplicateComments" : 0,
      "address1" : null,
      "address2" : null,
      "agencyId" : "CMS",
      "city" : null,
      "category" : "Association - Drug",
      "comment" : "<br/>See Attached Letter",
      "country" : "United States",
      "displayProperties" : [ {
        "name" : "pageCount",
        "label" : "Page Count",
        "tooltip" : "Number of pages In the content file"
      } ],
      "docAbstract" : null,
      "docketId" : "CMS-2022-0012",
      "documentType" : "Public Submission",
      "email" : null,
      "fax" : null,
      "field1" : null,
      "field2" : null,
      "fileFormats" : null,
      "firstName" : null,
      "govAgency" : null,
      "govAgencyType" : null,
      "objectId" : "0900006484f5abf0",
      "lastName" : null,
      "legacyId" : null,
      "modifyDate" : "2022-02-09T18:38:00Z",
      "organization" : null,
      "originalDocumentId" : null,
      "pageCount" : 1,
      "phone" : null,
      "postedDate" : "2022-02-09T05:00:00Z",
      "postmarkDate" : null,
      "reasonWithdrawn" : null,
      "receiveDate" : "2022-02-07T05:00:00Z",
      "restrictReason" : null,
      "restrictReasonType" : null,
      "stateProvinceRegion" : "MA",
      "submitterRep" : null,
      "submitterRepAddress" : null,
      "submitterRepCityState" : null,
      "subtype" : "Public Comment",
      "title" : "Comment on CMS-2022-0012-0001",
      "trackingNbr" : "kzd-19mm-s660",
      "withdrawn" : false,
      "zip" : null,
      "openForComment" : false
    },
    "relationships" : {
      "attachments" : {
        "links" : {
          "self" : "https://api.regulations.gov/v4/comments/CMS-2022-0012-0392/relationships/attachments",
          "related" : "https://api.regulations.gov/v4/comments/CMS-2022-0012-0392/attachments"
        }
      }
    }
  }
}

### Example of an JSON with attachment endpoint.
https://api.regulations.gov/v4/comments/CMS-2022-0012-0392/attachments?api_key=<API_KEY>
{
  "data" : [ {
    "id" : "0900006484f5abf1",
    "type" : "attachments",
    "links" : {
      "self" : "https://api.regulations.gov/v4/attachments/0900006484f5abf1"
    },
    "attributes" : {
      "agencyNote" : null,
      "authors" : null,
      "docAbstract" : null,
      "docOrder" : 1,
      "fileFormats" : [ {
        "fileUrl" : "https://downloads.regulations.gov/CMS-2022-0012-0392/attachment_1.pdf",
        "format" : "pdf",
        "size" : 85021
      }, {
        "fileUrl" : "https://downloads.regulations.gov/CMS-2022-0012-0392/attachment_1.docx",
        "format" : "docx",
        "size" : 29290
      } ],
      "modifyDate" : "2022-02-07T13:44:14Z",
      "publication" : null,
      "restrictReason" : null,
      "restrictReasonType" : null,
      "title" : "CMS"
    }
  } ]
}

### Example of an JSON with attachment endpoint but does not contain any attachments.
https://api.regulations.gov/v4/comments/CMS-2022-0012-0001/attachments?api_key=<API_KEY>
{
  "data" : [ ]
}