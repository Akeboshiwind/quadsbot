use json::JsonValue;
use std::time::Duration;

use crate::{Api, ApiError, Update};
use log::{debug, error};

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

impl Api {
    pub fn stream(&self) -> UpdateStreamIter {
        UpdateStreamIter {
            api: self,
            messages: vec![],
            offset: None,
            timeout: 60,
        }
    }
}
