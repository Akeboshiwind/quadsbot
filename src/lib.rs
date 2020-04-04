use chrono::{Local, TimeZone};
use telegram_bot::{prelude::*, Api, Message, MessageKind};

/// Return how many times the first character is repeated in a row
fn repeated_chars(text: &str) -> usize {
    let first_char = text.chars().next().unwrap();

    let mut count = 0;
    for c in text.chars() {
        if c == first_char {
            count += 1;
        } else {
            break;
        }
    }

    count
}

/// Format the input timestamp into HHMMSS format for easy 'check'ing
fn format_date(timestamp: &i64) -> String {
    let date = Local.timestamp(*timestamp, 0);
    date.format("%I%M%S").to_string()
}

/// Tests if n is quads
fn is_quads(n: usize) -> bool {
    n >= 4
}

/// Tests if n is sexts
fn is_sexts(n: usize) -> bool {
    n >= 6
}

#[derive(PartialEq, Debug)]
enum Action {
    Delete,
    Reply,
    None,
}

fn process_message(message: &Message) -> Action {
    if let MessageKind::Text { ref data, .. } = message.kind {
        let date = format_date(&message.date);

        println!("{}@{}: {}", message.from.first_name, date, data);

        let n = repeated_chars(&date);

        if is_quads(n) {
            let text_message = data.to_lowercase();
            if let Some(text_message) = text_message.get(0..5) {
                if (text_message == "quads" && is_quads(n))
                    || (text_message == "sexts" && is_sexts(n))
                {
                    return Action::Reply;
                }
            }
            return Action::None;
        }
    }
    Action::Delete
}

/// Handle incoming messages
///
/// If the bot has the ability to delete messages, it will delete all messages
/// not sent on at least 'quads'
///
/// If a message matches 'quads' and is sent on 'quads' then the bot will reply
/// to the message with 'checked'
///
/// If a message matches 'sexts' and is sent on 'sexts' then the bot will reply
/// to the message with 'checked'
pub async fn handle_message(api: &Api, message: &Message) {
    let action = process_message(message);

    match action {
        Action::None => {}
        Action::Reply => {
            if let Err(error) = api.send(message.text_reply("Checked")).await {
                println!("Failed to reply to message with error: {:?}", error);
            }
        }
        Action::Delete => {
            if let Err(error) = api.send(message.delete()).await {
                println!("Failed to delete message with error: {:?}", error);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    mod repeated_chars {
        use super::*;

        #[test]
        fn test_single_character() {
            let text = "1";
            assert_eq!(repeated_chars(&text), 1);
        }

        #[test]
        fn test_short_string() {
            let text = "11111";
            assert_eq!(repeated_chars(&text), 5);
        }

        #[test]
        fn test_non_repeating() {
            let text = "12131";
            assert_eq!(repeated_chars(&text), 1);
        }

        #[test]
        fn test_short_repeating() {
            let text = "1112131";
            assert_eq!(repeated_chars(&text), 3);
        }
    }

    mod format_date {
        use super::*;

        #[test]
        fn test_not_quads() {
            let timestamp = Local.ymd(2020, 1, 1).and_hms(1, 1, 1).timestamp();
            assert_eq!(format_date(&timestamp), "010101");
        }

        #[test]
        fn test_quads() {
            let timestamp = Local.ymd(2020, 1, 1).and_hms(11, 11, 1).timestamp();
            assert_eq!(format_date(&timestamp), "111101");
        }

        #[test]
        fn test_sexts() {
            let timestamp = Local.ymd(2020, 1, 1).and_hms(11, 11, 11).timestamp();
            assert_eq!(format_date(&timestamp), "111111");
        }
    }

    mod format_then_check_repeated {
        use super::*;

        #[test]
        fn test_end_to_end_quads() {
            let timestamp = Local.ymd(2020, 1, 1).and_hms(11, 11, 1).timestamp();
            let text = format_date(&timestamp);
            assert_eq!(repeated_chars(&text), 4);
        }

        #[test]
        fn test_end_to_end_sexts() {
            let timestamp = Local.ymd(2020, 1, 1).and_hms(11, 11, 11).timestamp();
            let text = format_date(&timestamp);
            assert_eq!(repeated_chars(&text), 6);
        }
    }

    mod process_message {
        use super::*;
        use telegram_bot::{Group, MessageChat, User};

        fn fake_message(timestamp: i64, text_message: String) -> Message {
            Message {
                id: 1.into(),
                from: User {
                    id: 1.into(),
                    first_name: "Test User".to_string(),
                    last_name: None,
                    username: None,
                    is_bot: false,
                    language_code: None,
                },
                date: timestamp,
                chat: MessageChat::Group(Group {
                    id: 1.into(),
                    title: "Test group".to_string(),
                    all_members_are_administrators: false,
                    invite_link: None,
                }),
                forward: None,
                reply_to_message: None,
                edit_date: None,
                kind: MessageKind::Text {
                    data: text_message,
                    entities: vec![],
                },
            }
        }

        mod action_delete {
            use super::*;

            #[test]
            fn test_not_on_quads() {
                let timestamp = Local.ymd(2020, 1, 1).and_hms(1, 1, 1).timestamp();
                let message = fake_message(timestamp, "Test Message".to_string());

                assert_eq!(process_message(&message), Action::Delete);
            }
        }

        mod action_none {
            use super::*;

            #[test]
            fn test_on_quads_not_checked() {
                let timestamp = Local.ymd(2020, 1, 1).and_hms(11, 11, 1).timestamp();
                let message = fake_message(timestamp, "Test Message".to_string());

                assert_eq!(process_message(&message), Action::None);
            }

            #[test]
            fn test_on_quads_dont_check_sexts() {
                let timestamp = Local.ymd(2020, 1, 1).and_hms(11, 11, 1).timestamp();
                let message = fake_message(timestamp, "sexts".to_string());

                assert_eq!(process_message(&message), Action::None);
            }

            #[test]
            fn test_on_sexts() {
                let timestamp = Local.ymd(2020, 1, 1).and_hms(11, 11, 11).timestamp();
                let message = fake_message(timestamp, "Test Message".to_string());

                assert_eq!(process_message(&message), Action::None);
            }
        }

        mod action_reply {
            use super::*;

            #[test]
            fn test_on_quads_checked_quads() {
                let timestamp = Local.ymd(2020, 1, 1).and_hms(11, 11, 1).timestamp();
                let message = fake_message(timestamp, "quads".to_string());

                assert_eq!(process_message(&message), Action::Reply);
            }

            #[test]
            fn test_on_quads_checked_quads_with_different_casing() {
                let timestamp = Local.ymd(2020, 1, 1).and_hms(11, 11, 1).timestamp();
                let message = fake_message(timestamp, "QuAdS".to_string());

                assert_eq!(process_message(&message), Action::Reply);
            }

            #[test]
            fn test_on_quads_check_begins_with_quads() {
                let timestamp = Local.ymd(2020, 1, 1).and_hms(11, 11, 1).timestamp();
                let message = fake_message(timestamp, "quads".to_string());

                assert_eq!(process_message(&message), Action::Reply);
            }

            #[test]
            fn test_on_sexts_checked_quads() {
                let timestamp = Local.ymd(2020, 1, 1).and_hms(11, 11, 11).timestamp();
                let message = fake_message(timestamp, "quads".to_string());

                assert_eq!(process_message(&message), Action::Reply);
            }

            #[test]
            fn test_on_sexts_checked_sexts() {
                let timestamp = Local.ymd(2020, 1, 1).and_hms(11, 11, 11).timestamp();
                let message = fake_message(timestamp, "sexts".to_string());

                assert_eq!(process_message(&message), Action::Reply);
            }
        }
    }
}
