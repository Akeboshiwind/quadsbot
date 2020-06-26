use crate::errors::TypeError;

use json::JsonValue;

#[derive(Debug)]
pub struct Chat {
    pub id: i64,
}

impl Chat {
    pub fn new(value: JsonValue) -> Result<Self, TypeError> {
        if let JsonValue::Object(obj) = value {
            let id = obj["id"]
                .as_i64()
                .ok_or_else(|| TypeError::FieldMissing("id".into()))?;

            Ok(Self { id })
        } else {
            Err(TypeError::InvalidJSONType("chat".into()))
        }
    }

    pub fn id(&self) -> &i64 {
        &self.id
    }
}
