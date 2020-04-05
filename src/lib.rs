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

#[derive(PartialEq, Debug)]
enum Check {
    Quads,
    Sexts,
    Other,
}

/// Perform a check on the input timestamp
///
/// If the timestamp starts four repeating numbers then it's Quads
/// If the timestamp starts six repeating numbers then it's Sexts
/// Otherwise then it's something else we don't care about
///
/// Checks in both 12h and 24h time formats
fn check(timestamp: &i64) -> Check {
    let date = Local.timestamp(*timestamp, 0);

    let date_12h = date.format("%I%M%S").to_string();
    let date_24h = date.format("%H%M%S").to_string();

    let n = {
        let n_12h = repeated_chars(&date_12h);
        let n_24h = repeated_chars(&date_24h);

        if n_12h > n_24h {
            n_12h
        } else {
            n_24h
        }
    };

    match n {
        4 | 5 => Check::Quads,
        6 => Check::Sexts,
        _ => Check::Other,
    }
}

#[derive(PartialEq, Debug)]
enum Action {
    Delete,
    Reply,
    None,
}

/// Work out the correct action to take for an input action
fn process_message(message: &Message) -> Action {
    let check = check(&message.date);

    match check {
        Check::Quads | Check::Sexts => {
            if let MessageKind::Text { ref data, .. } = message.kind {
                let text_message = data.to_lowercase();
                if let Some(text_message) = text_message.get(0..5) {
                    if (text_message == "quads")
                        || (text_message == "sexts" && check == Check::Sexts)
                    {
                        return Action::Reply;
                    }
                }
            }
            Action::None
        }
        _ => Action::Delete,
    }
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

    mod check {
        use super::*;

        #[test]
        fn test_not_quads() {
            let timestamp = Local.ymd(2020, 1, 1).and_hms(1, 1, 1).timestamp();
            assert_eq!(check(&timestamp), Check::Other);
        }

        #[test]
        fn test_morning_eleven_quads() {
            let timestamp = Local.ymd(2020, 1, 1).and_hms(11, 11, 1).timestamp();
            assert_eq!(check(&timestamp), Check::Quads);
        }

        #[test]
        fn test_evening_eleven_quads() {
            let timestamp = Local.ymd(2020, 1, 1).and_hms(23, 11, 1).timestamp();
            assert_eq!(check(&timestamp), Check::Quads);
        }

        #[test]
        fn test_evening_ten_quads() {
            let timestamp = Local.ymd(2020, 1, 1).and_hms(22, 22, 1).timestamp();
            assert_eq!(check(&timestamp), Check::Quads);
        }

        #[test]
        fn test_midnight_quads() {
            let timestamp = Local.ymd(2020, 1, 1).and_hms(0, 0, 1).timestamp();
            assert_eq!(check(&timestamp), Check::Quads);
        }

        #[test]
        fn test_sexts() {
            let timestamp = Local.ymd(2020, 1, 1).and_hms(11, 11, 11).timestamp();
            assert_eq!(check(&timestamp), Check::Sexts);
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

            #[test]
            fn test_quads_not_on_quads() {
                let timestamp = Local.ymd(2020, 1, 1).and_hms(1, 1, 1).timestamp();
                let message = fake_message(timestamp, "quads".to_string());

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
