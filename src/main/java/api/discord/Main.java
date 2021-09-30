package api.discord;

import auth.OAuthHelper;
import org.javacord.api.DiscordApi;
import org.javacord.api.DiscordApiBuilder;

public class Main {
    private static DiscordApi discordApi;


    public static void init(){
//        Initialize the Discord Api class
        discordApi = new DiscordApiBuilder().setToken(OAuthHelper.getDiscordToken()).login().join();
//        Add a listener to the api connection, adding this also enables message responding functionality
        discordApi.addListener(new Listener());
    }


}
