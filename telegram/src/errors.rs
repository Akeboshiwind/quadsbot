use thiserror::Error;

#[derive(Debug, Error)]
pub enum TypeError {
    #[error("Field {0} missing")]
    FieldMissing(String),
    #[error("Got invalid JSON type while trying to parse {0}")]
    InvalidJSONType(String),
}

#[derive(Debug, Error)]
pub enum ApiError {
    #[error("Failed to make the HTTP request: {source}")]
    Http {
        #[from]
        source: attohttpc::Error,
    },
    #[error("Failed to convert the result of an HTTP request {source}")]
    ConversionError {
        #[from]
        source: TypeError,
    },
    #[error("Failed to parse json {source}")]
    JsonError {
        #[from]
        source: json::Error,
    },
    #[error("Field missing in returned result")]
    MissingField,
    #[error("Error returned by the telegram api")]
    TelegramApi,
}

