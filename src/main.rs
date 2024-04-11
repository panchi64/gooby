use poise::serenity_prelude as serenity;

mod commands;
mod config;

#[derive(Debug)]
struct Data {} // User data, which is stored and accessible in all command invocations
type Error = Box<dyn std::error::Error + Send + Sync>;
type Context<'a> = poise::Context<'a, Data, Error>;


async fn on_error(error: poise::FrameworkError<'_, Data, Error>) {
    // Handle any errors that may occur
    println!("An error occurred: {:?}", error);
}

#[tokio::main]
async fn main() {
    let config = config::load_config();

    let framework = poise::Framework::builder()
        .options(poise::FrameworkOptions {
            commands: vec![
                commands::ping(),
                commands::roll(),
                commands::play(),
                commands::generate(),
                commands::mock(),
                commands::report(),
                commands::meme(),
            ],
            on_error: |error| Box::pin(on_error(error)),
            prefix_options: poise::PrefixFrameworkOptions {
                prefix: Some("!".into()),
                ..Default::default()
            },
            ..Default::default()
        })
        .intents(serenity::GatewayIntents::non_privileged())
        .setup(|ctx, _ready, framework| {
            Box::pin(async move {
                poise::builtins::register_globally(ctx, &framework.options().commands).await?;
                Ok(Data {})
            })
        })
        .build();

    let mut client = serenity::Client::builder(&config.discord_token, serenity::GatewayIntents::non_privileged())
        .event_handler(framework)
        .await
        .expect("Err creating client");

    if let Err(why) = client.start().await {
        println!("Client error: {:?}", why);
    }
}