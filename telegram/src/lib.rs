mod types;

pub use types::*;

use std::time::Duration;

use json::JsonValue;
use log::{debug, error};
use thiserror::Error;

const BASE_URL: &str = "https://api.telegram.org";

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

pub struct UpdateStreamIter<'api> {
    api: &'api Api,
    messages: Vec<Update>,
    offset: Option<i64>,
    timeout: u64,
}

impl<'api> UpdateStreamIter<'api> {
    fn get_updates(&mut self) -> Result<Vec<Update>, ApiError> {
        let body = {
            let mut body = json::object! {
                timeout: self.timeout
            };

            if let Some(offset) = self.offset {
                body["offset"] = (offset + 1).into();
            }

            body
        };

        let result = self.api.make_request_timeout(
            "getUpdates",
            body,
            Some(Duration::from_secs(2 * self.timeout.max(1))),
        )?;

        if let JsonValue::Array(mut updates) = result {
            let updates = updates
                .drain(0..)
                .map(Update::new)
                .collect::<Result<Vec<_>, _>>()?;

            if let Some(last) = updates.last() {
                self.offset = Some(last.update_id);
            }

            Ok(updates)
        } else {
            Err(ApiError::TelegramApi)
        }
    }
}

impl<'api> Iterator for UpdateStreamIter<'api> {
    type Item = Update;

    fn next(&mut self) -> Option<Update> {
        while self.messages.is_empty() {
            match self.get_updates() {
                Ok(mut updates) => {
                    debug!("Found {} message(s)", updates.len());
                    // If we recieve no messages we keep blocking
                    self.messages.append(&mut updates);
                }
                Err(err) => {
                    error!("Failed to get messages from api: {}", err);
                    // return None;
                }
            }
        }

        debug!("Returning a message");
        // We've just checked that messages isn't empty
        Some(self.messages.pop().unwrap())
    }
}

pub struct Api {
    token: String,
}

impl Api {
    pub fn new(token: String) -> Self {
        Self { token }
    }

    pub fn stream(&self) -> UpdateStreamIter {
        UpdateStreamIter {
            api: self,
            messages: vec![],
            offset: None,
            timeout: 60,
        }
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

    fn make_request(&self, method: &str, body: JsonValue) -> Result<JsonValue, ApiError> {
        self.make_request_timeout(method, body, None)
    }

    fn make_request_timeout(
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
