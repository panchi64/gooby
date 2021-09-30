package auth;

import io.github.cdimascio.dotenv.Dotenv;

public class oAuthHelper {
    //    Read from the environment variables file
    private static Dotenv env = Dotenv.load();

    private static String DISCORD_AUTH = env.get("DISCORD_AUTH");
    private static String GOOGLE_AUTH = env.get("GOOGLE_AUTH");
    private static String SOUNDCLOUD_AUTH = env.get("SOUNDCLOUD_AUTH");
    private static String YOUTUBE_AUTH = env.get("YOUTUBE_AUTH");
    private static String SPOTIFY_AUTH = env.get("SPOTIFY_AUTH");


    static String getAuthDiscord(){
        return DISCORD_AUTH;
    }
    static String getAuthGoogle(){
        return GOOGLE_AUTH;
    }
    static String getAuthSoundCloud(){
        return SOUNDCLOUD_AUTH;
    }
    static String getAuthYoutube(){
        return YOUTUBE_AUTH;
    }
    static String getAuthSpotify(){
        return SPOTIFY_AUTH;
    }
}
