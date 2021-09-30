package api.discord;

import auth.OAuthHelper;
import org.javacord.api.DiscordApi;
import org.javacord.api.DiscordApiBuilder;
import org.javacord.api.event.message.MessageCreateEvent;

import java.util.HashMap;
import java.util.Map;

//Contains all the functionality for this platform
public class Main {
    private static DiscordApi discordApi;

    public static void init(){
//        Initialize the Discord Api class
        discordApi = new DiscordApiBuilder().setToken(OAuthHelper.getDiscordToken()).login().join();
//        Add a listener to the api connection, adding this also enables message responding functionality
        discordApi.addListener(new Listener());
    }

/*
    Big caveat to responding to a trigger this way!
    The more triggers you add, the slower it will become, since it has to compare every single trigger and see if it is found
    in the message received.

    I.E. It has a Big-O notation of O(n) for every message received
 */
    /**
     * Responds when a certain text prompt is "seen" with the listener in a message. It is case-insensitive and can
     * ignore messages without whitespace.
     * @param event A given MessageCreateEvent
     */
    static void respondToTrigger(MessageCreateEvent event) {
//        Map containing all the triggers (Key) and responses (Value)
        Map<String, String> triggers = new HashMap<>();
        triggers.put("!soundTheHorn","https://media.giphy.com/media/rmQPNw0XuoGT8CyhCH/giphy.gif");
        triggers.put("!shakeIt","https://media.giphy.com/media/DqhwoR9RHm3EA/giphy.gif");
        triggers.put("gamer time?","https://media.giphy.com/media/4aFQ6F8s4wgz6/giphy.gif");

//        Message content set to lowercase for comparison
        String comparableMessage = event.getMessageContent().toLowerCase();

//        Iterate through the map and find the first trigger, if any
        int tempIndex = -1;
        String firstTrigger = null;
        for (String trigger: triggers.keySet()) {

//            This if statement converts the listened message to lowercase and finds the first prompt in the message
            if (comparableMessage.contains(trigger.toLowerCase())){
//                Temporarily keep the index of the command
                int triggerIndex = comparableMessage.indexOf(trigger.toLowerCase());
                if (tempIndex < 0){
                    firstTrigger = trigger;
                    tempIndex = triggerIndex;
                } else if (triggerIndex < tempIndex){
                    firstTrigger = trigger;
                    tempIndex = triggerIndex;
                }
            }
        }

//        After iterating and finding the first trigger, send the response to said trigger
        if ((firstTrigger != null) && (tempIndex != -1))
            event.getChannel().sendMessage(triggers.get(firstTrigger));
    }
}
