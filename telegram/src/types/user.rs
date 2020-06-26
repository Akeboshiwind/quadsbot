use crate::errors::TypeError;

use json::JsonValue;

#[derive(Debug)]
pub struct User {
    pub id: i64,
    pub first_name: String,
}

impl User {
    pub fn new(value: JsonValue) -> Result<Self, TypeError> {
        if let JsonValue::Object(obj) = value {
            let id = obj["id"]
                .as_i64()
                .ok_or_else(|| TypeError::FieldMissing("id".into()))?;

            let first_name = obj["first_name"]
                .as_str()
                .ok_or_else(|| TypeError::FieldMissing("first_name".into()))?
                .to_string();

            Ok(Self { id, first_name })
        } else {
            Err(TypeError::InvalidJSONType("user".into()))
        }
    }
}
