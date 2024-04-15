// src/config.rs

use serde::Deserialize;

#[derive(Deserialize)]
pub struct Config {
    pub discord: DiscordConfig,
    pub openai: OpenAIConfig,
    pub spotify: SpotifyConfig,
    pub youtube: YouTubeConfig,
}

#[derive(Deserialize)]
pub struct DiscordConfig {
    pub api_key: String,
    pub api_version: String,
    pub api_portal: String,
    pub server_id: String,
    pub report_channel_id: String,
}

#[derive(Deserialize)]
pub struct OpenAIConfig {
    pub api_key: String,
    pub api_version: String,
    pub api_portal: String,
    pub api_chat_model: String,
}

#[derive(Deserialize)]
pub struct SpotifyConfig {
    pub api_key: String,
    pub api_portal: String,
    pub api_version: String,
    pub api_portal_search: String,
    pub api_portal_tracks: String,
    pub api_portal_playlists: String,
}

#[derive(Deserialize)]
pub struct YouTubeConfig {
    pub api_key: String,
    pub api_portal: String,
    pub api_version: String,
}

pub fn load_config() -> Config {
    let config_str = std::fs::read_to_string("config.toml").expect("Failed to read config.toml");
    toml::from_str(&config_str).expect("Failed to parse config.toml")
}
