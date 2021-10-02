package api.discord;

import auth.OAuthHelper;
import org.javacord.api.DiscordApi;
import org.javacord.api.DiscordApiBuilder;
import org.javacord.api.event.message.MessageCreateEvent;
import org.javacord.api.interaction.SlashCommand;
import org.javacord.api.interaction.SlashCommandInteraction;
import org.javacord.api.listener.message.MessageCreateListener;

public class MessageListener implements MessageCreateListener {
    DiscordApi connection = new DiscordApiBuilder().setToken(OAuthHelper.getDiscordToken()).login().join();

    @Override
    public void onMessageCreate(MessageCreateEvent event) {
//        If the event is a "normal" chat message, send it to the trigger response method for evaluation
            api.discord.Main.respondToTrigger(event);
    }
}