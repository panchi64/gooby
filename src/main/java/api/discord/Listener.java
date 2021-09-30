package api.discord;

import auth.OAuthHelper;
import org.javacord.api.DiscordApi;
import org.javacord.api.DiscordApiBuilder;
import org.javacord.api.event.message.MessageCreateEvent;
import org.javacord.api.listener.message.MessageCreateListener;

public class Listener implements MessageCreateListener {
    DiscordApi connection = new DiscordApiBuilder().setToken(OAuthHelper.getDiscordToken()).login().join();

//    This "responder" are for special cases where a / command is not feasible or easy to implement
    @Override
    public void onMessageCreate(MessageCreateEvent event) {
//        Prompts that can trigger messages from the bot
        answer(event,
                "!soundTheHorn",
                "https://media.giphy.com/media/rmQPNw0XuoGT8CyhCH/giphy.gif"
        );
        answer(event,
                "!shakeIt",
                "https://media.giphy.com/media/DqhwoR9RHm3EA/giphy.gif"
                );
        answer(event,
                "gamer time?",
                "https://media.giphy.com/media/tIeCLkB8geYtW/giphy.gif"
                );
    }

    /**
     * Responds when a certain prompt is "seen" with the listener
     * @param event A given MessageCreateEvent
     * @param prompt Triggers a response
     * @param response Content returned on trigger
     */
    private void answer(MessageCreateEvent event, String prompt, String response) {
//        TODO: Make it so that prompt can be found in any type of message
//              (Possible implementation can be to convert the whole prompt to lowercase and see if the trigger is within it)
        if(event.getMessageContent().contains(prompt)){
            event.getChannel().sendMessage(response);
        }
    }
}
