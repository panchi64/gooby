package api.discord;

import auth.OAuthHelper;
import org.javacord.api.DiscordApi;
import org.javacord.api.DiscordApiBuilder;
import org.javacord.api.event.message.MessageCreateEvent;
import org.javacord.api.listener.message.MessageCreateListener;

public class Listener implements MessageCreateListener {
    DiscordApi connection = new DiscordApiBuilder().setToken(OAuthHelper.getDiscordToken()).login().join();

    @Override
    public void onMessageCreate(MessageCreateEvent event) {
//        Responds to a trigger prompt when / commands are not a feasible option
        api.discord.Main.respondToTrigger(event);
    }
}