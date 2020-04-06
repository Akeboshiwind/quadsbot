use log::info;
use pretty_env_logger;
use std::env;

use futures::StreamExt;
use telegram_bot::{Api, Error, UpdateKind};

use quadsbot::*;

#[tokio::main]
async fn main() -> Result<(), Error> {
    pretty_env_logger::init();

    let pkg_version = env!("CARGO_PKG_VERSION");
    info!("QuadsBot v{}", pkg_version);

    let token = env::var("TELEGRAM_BOT_TOKEN").expect("TELEGRAM_BOT_TOKEN not set");
    let api = Api::new(token);

    info!("Start listening for events...");
    let mut stream = api.stream();
    while let Some(update) = stream.next().await {
        // If the received update contains a new message...
        if let Ok(update) = update {
            if let UpdateKind::Message(message) = update.kind {
                handle_message(&api, &message).await;
            }
        }
    }

    Ok(())
}
