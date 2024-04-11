use serde::Deserialize;

// README: Look at the example_config.toml for a more legible understanding of the structure.

#[derive(Deserialize)]
pub struct Config {
    pub discord: DiscordConfig,
    pub openai: OpenAIConfig,
    pub spotify: SpotifyConfig,
    pub youtube: YouTubeConfig,
}

#[derive(Deserialize)]
pub struct DiscordConfig {
    pub api: DiscordApiConfig,
    pub server: DiscordServerConfig,
}

#[derive(Deserialize)]
pub struct DiscordApiConfig {
    pub key: String,
    pub version: String,
    pub portal: String,
}

#[derive(Deserialize)]
pub struct DiscordServerConfig {
    pub id: String,
}

#[derive(Deserialize)]
pub struct OpenAIConfig {
    pub api: OpenAIApiConfig,
}

#[derive(Deserialize)]
pub struct OpenAIApiConfig {
    pub key: String,
    pub version: String,
    pub portal: String,
    pub chat: OpenAIChatConfig,
}

#[derive(Deserialize)]
pub struct OpenAIChatConfig {
    pub model: String,
}

#[derive(Deserialize)]
pub struct SpotifyConfig {
    pub api: SpotifyApiConfig,
}

#[derive(Deserialize)]
pub struct SpotifyApiConfig {
    pub key: String,
    pub portal: String,
    pub version: String,
    pub portal_search: String,
    pub portal_tracks: String,
    pub portal_playlists: String,
}

#[derive(Deserialize)]
pub struct YouTubeConfig {
    pub api: YouTubeApiConfig,
}

#[derive(Deserialize)]
pub struct YouTubeApiConfig {
    pub key: String,
    pub portal: String,
    pub version: String,
}

pub fn load_config() -> Config {
    let config_str = std::fs::read_to_string("config.toml").expect("Failed to read config.toml");
    toml::from_str(&config_str).expect("Failed to parse config.toml")
}