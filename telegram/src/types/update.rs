use crate::errors::TypeError;
use crate::types::Message;

use json::JsonValue;

#[derive(Debug)]
pub struct Update {
    pub update_id: i64,
    pub message: Option<Message>,
}

impl Update {
    pub fn new(value: JsonValue) -> Result<Self, TypeError> {
        if let JsonValue::Object(mut obj) = value {
            let update_id = obj["update_id"]
                .as_i64()
                .ok_or_else(|| TypeError::FieldMissing("update_id".into()))?;

            let message = {
                let message = obj["message"].take();
                if message.is_object() {
                    Some(Message::new(message)?)
                } else {
                    None
                }
            };

            Ok(Self { update_id, message })
        } else {
            Err(TypeError::InvalidJSONType("update".into()))
        }
    }
}

