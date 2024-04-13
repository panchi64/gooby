use crate::{Context, Error};
use poise::{serenity_prelude as serenity};
use rand::{Rng, SeedableRng};
use serenity::all::{Mentionable};

/// Ping command
#[poise::command(slash_command)]
pub async fn ping(ctx: Context<'_>) -> Result<(), Error> {
    ctx.say("Pong!").await?;
    Ok(())
}

/// Roll dice command
#[poise::command(slash_command)]
pub async fn roll(ctx: Context<'_>, #[description = "Number of dice"] num_dice: u32, #[description = "Number of sides"] num_sides: u32) -> Result<(), Error> {
    let mut rng = rand::rngs::StdRng::from_entropy();
    let rolls: Vec<u32> = (0..num_dice).map(|_| rng.gen_range(1..=num_sides)).collect();
    let total: u32 = rolls.iter().sum();

    ctx.say(format!("Rolled {} dice with {} sides each:\n{:?}\nTotal: {}", num_dice, num_sides, rolls, total)).await?;
    Ok(())
}

/// Play music command
#[poise::command(slash_command)]
pub async fn play(ctx: Context<'_>, #[description = "YouTube or Spotify URL"] url: String) -> Result<(), Error> {
    ctx.say(format!("Playing music from: {}", url)).await?;
    Ok(())
}

/// Generate image command
#[poise::command(slash_command)]
pub async fn generate(ctx: Context<'_>, #[description = "Image description"] description: String) -> Result<(), Error> {
    ctx.say(format!("Generating image for: {}", description)).await?;
    Ok(())
}

/// Mock user's latest message command
#[poise::command(slash_command)]
pub async fn mock_user(ctx: Context<'_>, #[description = "User to mock"] user: serenity::User) -> Result<(), Error> {
    todo!()
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
#[poise::command(slash_command)]
pub async fn report(ctx: Context<'_>, #[description = "User to report"] user: serenity::User, #[description = "Reason for the report"] reason: String) -> Result<(), Error> {
    ctx.say(format!("Reported user {} for reason: {}", user.mention(), reason)).await?;
    Ok(())
}

/// Meme generation command
#[poise::command(slash_command)]
pub async fn meme(ctx: Context<'_>, #[description = "Meme template"] template: String, #[description = "Top text"] top_text: String, #[description = "Bottom text"] bottom_text: String) -> Result<(), Error> {
    println!("Generating meme {} for {}", template, &ctx.author().name);
    Ok(())
}