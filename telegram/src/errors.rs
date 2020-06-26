use std::fmt;

#[derive(Debug)]
pub enum TypeError {
    FieldMissing(String),
    InvalidJSONType(String),
}

impl std::error::Error for TypeError {}

impl fmt::Display for TypeError {
    fn fmt(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
        match self {
            TypeError::FieldMissing(field) => write!(formatter, "Field {} missing", field),
            TypeError::InvalidJSONType(json_type) => write!(
                formatter,
                "Got invalid JSON type while trying to parse {}",
                json_type
            ),
        }
    }
}

#[derive(Debug)]
pub enum ApiError {
    Http { source: attohttpc::Error },
    ConversionError { source: TypeError },
    JsonError { source: json::Error },
    MissingField,
    TelegramApi,
}

impl std::error::Error for ApiError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            ApiError::Http { source } => Some(source),
            ApiError::ConversionError { source } => Some(source),
            ApiError::JsonError { source } => Some(source),
            ApiError::MissingField => None,
            ApiError::TelegramApi => None,
        }
    }
}

impl fmt::Display for ApiError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter) -> fmt::Result {
        match self {
            ApiError::Http { source } => {
                write!(formatter, "Failed to make the HTTP request: {}", source)
            }
            ApiError::ConversionError { source } => write!(
                formatter,
                "Failed to convert the result of an HTTP request: {}",
                source
            ),
            ApiError::JsonError { source } => write!(formatter, "Failed to parse json: {}", source),
            ApiError::MissingField {} => write!(formatter, "Field missing in returned result"),
            ApiError::TelegramApi {} => write!(formatter, "Error returned by the telegram api"),
        }
    }
}

impl std::convert::From<attohttpc::Error> for ApiError {
    fn from(source: attohttpc::Error) -> Self {
        ApiError::Http { source }
    }
}

impl std::convert::From<TypeError> for ApiError {
    fn from(source: TypeError) -> Self {
        ApiError::ConversionError { source }
    }
}

impl std::convert::From<json::Error> for ApiError {
    fn from(source: json::Error) -> Self {
        ApiError::JsonError { source }
    }
}
