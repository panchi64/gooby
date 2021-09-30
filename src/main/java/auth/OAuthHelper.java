package auth;

import io.github.cdimascio.dotenv.Dotenv;

public class OAuthHelper {
    //    Read from the environment variables file
    private static final Dotenv env = Dotenv.load();

    private static final String DISCORD_AUTH_ID = env.get("DISCORD_AUTH");
    private static final String DISCORD_TOKEN = env.get("DISCORD_TOKEN");

    private static final String GOOGLE_AUTH_ID = env.get("GOOGLE_AUTH");
    private static final String SOUNDCLOUD_AUTH_ID = env.get("SOUNDCLOUD_AUTH");
    private static final String YOUTUBE_AUTH_ID = env.get("YOUTUBE_AUTH");
    private static final String SPOTIFY_AUTH_ID = env.get("SPOTIFY_AUTH");

//  Enables the previous variables to be read only

    /**
     * Gets the Bot Token for the Discord Platform from an environmental variable
     *
     * @return String containing the Bot token for Discord
     */
    public static String getDiscordToken(){ return DISCORD_TOKEN; }
    /**
     *  Gets the Client ID for the Discord Platform from an environment variable
     *
     * @return String containing the Client ID for Discord
     */
    public static String getAuthDiscordID(){ return DISCORD_AUTH_ID; }

    /**
     * Gets the Client ID for the Google API from an environment variable.
     * @return String containing the Google API Client ID
     */
    public static String getAuthGoogleID(){ return GOOGLE_AUTH_ID; }

    /**
     * Gets the Client ID for Soundcloud from an environment variable.
     * @return String containing the Soundcloud Client ID
     */
    public static String getAuthSoundCloudID(){ return SOUNDCLOUD_AUTH_ID; }

    /**
     * Gets the Client ID for YouTube from an environment variable.
     * @return String containing the YouTube Client ID
     */
    public static String getAuthYoutubeID(){ return YOUTUBE_AUTH_ID; }

    /**
     * Gets the Client ID for Spotify from an environment variable.
     * @return String containing the Spotify Client ID
     */
    public static String getAuthSpotifyID(){ return SPOTIFY_AUTH_ID; }
}
