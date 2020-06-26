use crate::errors::TypeError;
use crate::types::{Chat, User};

use json::JsonValue;

#[derive(Debug)]
pub struct Message {
    pub message_id: i64,
    pub from: Option<User>,
    pub date: i64,
    pub chat: Chat,
    pub text: Option<String>,
}

impl Message {
    pub fn new(value: JsonValue) -> Result<Self, TypeError> {
        if let JsonValue::Object(mut obj) = value {
            let message_id = obj["message_id"]
                .as_i64()
                .ok_or_else(|| TypeError::FieldMissing("message_id".into()))?;

            let from = {
                let from = obj["from"].take();
                if from.is_object() {
                    Some(User::new(from)?)
                } else {
                    None
                }
            };

            let date = obj["date"]
                .as_i64()
                .ok_or_else(|| TypeError::FieldMissing("date".into()))?;

            let chat = Chat::new(obj["chat"].take())?;

            let text = obj["text"].as_str().map(str::to_string);

            Ok(Self {
                message_id,
                from,
                date,
                chat,
                text,
            })
        } else {
            Err(TypeError::InvalidJSONType("message".into()))
        }
    }
}
