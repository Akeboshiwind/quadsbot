use log::info;
use std::env;

use telegram::Api;

use quadsbot::*;

fn main() {
    env_logger::init();

    let pkg_version = env!("CARGO_PKG_VERSION");
    info!("QuadsBot v{}", pkg_version);

    let token = env::var("TELEGRAM_BOT_TOKEN").expect("TELEGRAM_BOT_TOKEN not set");
    let api = Api::new(token);

    info!("Start listening for events...");
    for update in api.stream() {
        // If the received update contains a new message...
        if let Some(message) = update.message {
            handle_message(&api, &message);
        }
    }
}
