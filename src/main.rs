mod commands;
mod config;
mod api;

use poise::serenity_prelude as serenity;
use serenity::prelude::GatewayIntents;

type Error = Box<dyn std::error::Error + Send + Sync>;
type Context<'a> = poise::Context<'a, UserData, Error>;

pub struct UserData {}

async fn on_error(error: poise::FrameworkError<'_, UserData, Error>) {
    // Only take in errors we want customized.
    // The rest are forwarded to the default handler.
    match error {
        poise::FrameworkError::Setup { error, .. } => panic!("Failed to start bot: {:?}", error),
        poise::FrameworkError::Command { error, ctx, .. } => {
            println!("Error in command `{}`: {:?}", ctx.command().name, error);
        }
        error => {
            if let Err(e) = poise::builtins::on_error(error).await {
                println!("Error while handling error: {}", e);
            }
        }
    }
}

#[tokio::main]
async fn main() {
    let config = config::load_config();

    let options = poise::FrameworkOptions {
        commands: vec![
            commands::dice_roll(),
            commands::play(),
            // commands::generate(),
            commands::mock_user(),
            commands::report(),
            // commands::meme(),
        ],
        prefix_options: poise::PrefixFrameworkOptions {
            prefix: Some("!".into()),
            additional_prefixes: vec![
                poise::Prefix::Literal("-"),
                poise::Prefix::Literal("$"),
                poise::Prefix::Literal("?"),
            ],
            case_insensitive_commands: true,
            execute_untracked_edits: true,
            ..Default::default()
        },
        on_error: |error| Box::pin(on_error(error)),
        pre_command: |ctx| {
            Box::pin(async move {
                println!(
                    "Got da \"{}\" command. Gettin' right on it...",
                    ctx.command().qualified_name
                );
            })
        },

        post_command: |ctx| {
            Box::pin(async move {
                println!(
                    "\"{}\" command is done big boss!",
                    ctx.command().qualified_name
                );
            })
        },
        ..Default::default()
    };

    let framework = poise::Framework::builder()
        .options(options)
        .setup(move |ctx, _ready, framework| {
            Box::pin(async move {
                println!(
                    "*yaaawwwnnn* Alrighty! {} is logged in and ready to go boss.",
                    _ready.user.name
                );
                poise::builtins::register_globally(ctx, &framework.options().commands).await?;
                Ok(UserData {})
            })
        })
        .build();

    let intents =
        GatewayIntents::non_privileged() | GatewayIntents::MESSAGE_CONTENT | GatewayIntents::DIRECT_MESSAGES;

    let mut client = serenity::Client::builder(&config.discord.api_key, intents)
        .framework(framework)
        .await
        .expect("Error creating client");

    if let Err(why) = client.start().await {
        println!("Client error: {:?}", why);
    }
}
