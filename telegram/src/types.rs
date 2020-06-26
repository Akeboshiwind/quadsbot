use json::JsonValue;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum TypeError {
    #[error("Field {0} missing")]
    FieldMissing(String),
    #[error("Got invalid JSON type while trying to parse {0}")]
    InvalidJSONType(String),
}

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

