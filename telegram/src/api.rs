use crate::errors::ApiError;
use crate::types::*;

use json::JsonValue;
use std::time::Duration;

const BASE_URL: &str = "https://api.telegram.org";

pub struct Api {
    token: String,
}

impl Api {
    pub fn new(token: String) -> Self {
        Self { token }
    }

    pub fn send_message(
        &self,
        chat_id: i64,
        text: String,
        reply_to_message_id: Option<i64>,
    ) -> Result<Message, ApiError> {
        log::info!("Making body");
        let body = {
            let mut body = json::object! {
                chat_id: chat_id,
                text: text,
            };

            if let Some(reply_to_message_id) = reply_to_message_id {
                body["reply_to_message_id"] = reply_to_message_id.into();
            }

            body
        };

        log::info!("Making request");
        let result = self.make_request("sendMessage", body)?;

        log::info!("Returning result");
        Ok(Message::new(result)?)
    }

    pub fn delete_message(&self, chat_id: i64, message_id: i64) -> Result<(), ApiError> {
        let body = json::object! {
            chat_id: chat_id,
            message_id: message_id,
        };

        self.make_request("deleteMessage", body)?;

        Ok(())
    }

    pub fn make_request(&self, method: &str, body: JsonValue) -> Result<JsonValue, ApiError> {
        self.make_request_timeout(method, body, None)
    }

    pub fn make_request_timeout(
        &self,
        method: &str,
        body: JsonValue,
        timeout: Option<Duration>,
    ) -> Result<JsonValue, ApiError> {
        // Build request
        let request = attohttpc::post(format!("{}/bot{}/{}", BASE_URL, self.token, method))
            .text(body.dump())
            .connect_timeout(timeout.unwrap_or(Duration::from_secs(30)))
            .try_header_append("Content-Type", "application/json")?;

        // Make request
        let ret = request.send()?;

        // Process request
        let mut wrapper = json::parse(&ret.text()?)?;

        let ok = wrapper["ok"]
            .as_bool()
            .ok_or_else(|| ApiError::MissingField)?;

        if ok {
            Ok(wrapper["result"].take())
        } else {
            Err(ApiError::TelegramApi)
        }
    }
}
