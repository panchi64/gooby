use crate::config;
use crate::{Context, Error};
use serenity::all::{Color, CreateEmbed};
use poise::serenity_prelude as serenity;
use poise::Modal;
use rand::{Rng, SeedableRng};
use serenity::all::{CreateMessage, GetMessages, Mentionable};
use serenity::model::Permissions;
use std::time::Duration;

/// Roll dice command
#[poise::command(prefix_command, slash_command, rename = "roll")]
pub async fn dice_roll(
    ctx: Context<'_>,
    #[description = "Number of dice"] dice_amount: u32,
    #[description = "Number of sides"] dice_type: u32,
) -> Result<(), Error> {
    let mut rng = rand::rngs::StdRng::from_entropy();
    let rolls: Vec<u32> = (0..dice_amount)
        .map(|_| rng.gen_range(1..=dice_type))
        .collect();
    let total: u32 = rolls.iter().sum();

    ctx.say(format!(
        "Rolled {}-d{}\n**Total: {}**\n*{:?}*",
        dice_amount, dice_type, total, rolls
    ))
        .await?;
    Ok(())
}

/// Play music command
#[poise::command(slash_command)]
pub async fn play(
    ctx: Context<'_>,
    #[description = "YouTube or Spotify URL"] url: String,
) -> Result<(), Error> {
    ctx.say(format!("Playing music from: {}", url)).await?;
    Ok(())
}

/// Generate image command
#[poise::command(slash_command)]
pub async fn generate(
    ctx: Context<'_>,
    #[description = "Image description"] description: String,
) -> Result<(), Error> {
    ctx.say(format!("Generating image for: {}", description))
        .await?;
    Ok(())
}

/// Mock user's latest message command
#[poise::command(slash_command)]
pub async fn mock_user(
    ctx: Context<'_>,
    #[description = "User to mock"] user: serenity::User,
) -> Result<(), Error> {
    let guild_id = ctx.guild_id().unwrap();
    let channels = guild_id.channels(&ctx.serenity_context().http).await?;

    for (channel_id, _) in channels {
        let channel = channel_id.to_channel(&ctx.serenity_context().http).await?;

        if let serenity::model::channel::Channel::Guild(guild_channel) = channel {
            let messages = guild_channel
                .messages(
                    &ctx.serenity_context().http,
                    GetMessages::limit(GetMessages::new(), 100),
                )
                .await?;

            for message in messages {
                if message.author.id == user.id {
                    let mocked_text = mock_text(&message.content);
                    ctx.say(mocked_text.to_string()).await?;
                    channel_id
                        .send_message(
                            &ctx.serenity_context().http,
                            CreateMessage::new()
                                .content("https://tenor.com/view/kekwtf-gif-18599263"),
                        )
                        .await?;
                    return Ok(());
                }
            }
        }
    }

    ctx.say(format!(
        "No recent message found for user {}",
        user.mention()
    ))
        .await?;
    Ok(())
}

fn mock_text(text: &str) -> String {
    let mut mocked = String::new();
    for (i, c) in text.chars().enumerate() {
        if i % 2 == 0 {
            mocked.push(c.to_ascii_uppercase());
        } else {
            mocked.push(c.to_ascii_lowercase());
        }
    }
    mocked
}

/// Report command
// Bless the soul of whoever wrote this
// https://github.com/chrisliebaer/kitmatheinfo-bot/blob/f83786cd24ca41523edbd9bb0a5cc0868ecdbd40/src/moderation.rs#L26
// without you, I would have never understood how the modal execution works.
// It was so hard to even find useful documentation for it.
#[poise::command(context_menu_command = "Report", ephemeral)]
pub async fn report(
    ctx: Context<'_>,
    #[description = "Report a user's message"] msg: serenity::Message,
) -> Result<(), Error> {
    let app_ctx = match ctx {
        Context::Application(ctx) => ctx,
        Context::Prefix(_) => {
            unreachable!("This command is only available as a context menu command.")
        }
    };

    let report = poise::execute_modal::<_, _, ReportReasonModal>(
        app_ctx,
        None,
        Some(Duration::from_secs(120)),
    )
        .await?;
    
    ctx.defer().await?;

    let terminal_report: String = format!("\n\tReceived a report for the following message:\n\tContent: {}\n\tSender: {} | {}\n\tSubmitted at: {}\n\tReason: {}\n",
                                          &msg.content, &msg.author.name, &msg.author, &msg.timestamp, &report.as_ref().unwrap().reason);

    let report_embed_msg = CreateEmbed::new()
        .title("Reported Message")
        .description("A  user message has been reported. Details below")
        .fields(vec![
            ("Content", msg.content.to_string(), true),
            ("Sent by", msg.author.to_string().clone(), true),
        ])
        .fields(vec![
            ("Message Timestamp", format!("<t:{}>", &msg.timestamp.timestamp()), true),
            ("Original Message",
             format!("[Jump to Message](https://discord.com/channels/{:?}/{}/{})",
                     &ctx.guild_id().unwrap().get(),
                     &msg.channel_id,
                     &msg.id)
             ,true),
            ("Reason", report.clone().unwrap().reason, false)
        ])
        .color(Color::GOLD);
    println!("{}", terminal_report);

    let config = config::load_config();
    let report_channel_id = config.discord.report_channel_id;

    let send_report = async {
        if !report_channel_id.is_empty() {
            let channel_id = serenity::ChannelId::new(report_channel_id.parse().unwrap());
            channel_id
                .send_message(
                    &ctx.serenity_context().http,
                    CreateMessage::new().add_embed(report_embed_msg),
                )
                .await?;
        } else {
            let guild_id = ctx.guild_id().unwrap();
            println!("Guild ID: {}", guild_id);

            match guild_id.to_partial_guild(&ctx.serenity_context().http).await {
                Ok(guild) => {
                    println!("Fetched partial guild: {}", guild.name);

                    match guild.members(&ctx.serenity_context().http, None, None).await {
                        Ok(members) => {
                            println!("Fetched {} members", members.len());

                            for member in members {
                                if let Ok(permissions) = member.permissions(ctx.serenity_context()) {
                                    if permissions.contains(Permissions::ADMINISTRATOR | Permissions::KICK_MEMBERS | Permissions::BAN_MEMBERS | Permissions::MANAGE_MESSAGES) {
                                        println!("Attempting to DM moderator: {}", member.user.tag());

                                        if let Err(err) = member.user.dm(&ctx.serenity_context().http, CreateMessage::new().content("Hiya! I've received a report for a message. Here's the report:").add_embed(report_embed_msg.clone())).await {
                                            println!("Failed to send DM to moderator {}: {:?}", member.user.tag(), err);
                                        } else {
                                            println!("DM sent to moderator: {}", member.user.tag());
                                        }
                                    }
                                }
                            }
                        }
                        Err(err) => {
                            println!("Failed to fetch members: {:?}", err);
                            return Err(Box::new(err));
                        }
                    }
                }
                Err(err) => {
                    println!("Failed to fetch partial guild: {:?}", err);
                    return Err(Box::new(err));
                }
            }
        }

        msg.react(
            &ctx.serenity_context().http,
            serenity::ReactionType::from('⚠'),
        )
            .await?;

        ctx.say("Goobstah got ur report. Zanks!").await?;

        Ok(())
    };

    if let Err(err) = send_report.await {
        eprintln!("Error while sending report: {:?}", err);
        ctx.say("Yowsaz I fumbled. Gonna go check what it was. Try again in a bit!").await?;
    }

    Ok(())
}

#[derive(Debug, Modal, Clone)]
#[name = "Report Reason"]
struct ReportReasonModal {
    #[name = "Report"]
    #[placeholder = "Enter the reason for the report"]
    #[min_length = 1]
    #[max_length = 500]
    reason: String,
}

/// Meme generation command
#[poise::command(slash_command)]
pub async fn meme(
    ctx: Context<'_>,
    #[description = "Meme template"] template: String,
    #[description = "Top text"] top_text: String,
    #[description = "Bottom text"] bottom_text: String,
) -> Result<(), Error> {
    println!("Generating meme {} for {}", template, &ctx.author().name);
    Ok(())
}
