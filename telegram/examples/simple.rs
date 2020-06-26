use std::env;

fn main() {
    env_logger::init();

    let api_key = env::var("API_KEY").expect("API_KEY must be set for this example to work");

    let api = telegram::Api::new(api_key);

    for update in api.stream() {
        if let Some(message) = update.message {
            println!("Replying...");

            api.send_message(
                message.chat.id,
                "My message".to_string(),
                Some(message.message_id),
            )
            .unwrap();
        }
    }
}
