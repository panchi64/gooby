package api.discord;

import auth.OAuthHelper;
import org.javacord.api.DiscordApi;
import org.javacord.api.DiscordApiBuilder;
import org.javacord.api.entity.channel.TextChannel;
import org.javacord.api.entity.message.MessageBuilder;
import org.javacord.api.entity.message.component.ActionRow;
import org.javacord.api.entity.message.component.Button;
import org.javacord.api.event.message.MessageCreateEvent;
import org.javacord.api.interaction.SlashCommand;
import org.javacord.api.interaction.SlashCommandInteraction;
import org.javacord.api.interaction.SlashCommandOption;
import org.javacord.api.interaction.SlashCommandOptionType;

import java.util.*;

//Contains all the functionality for this platform
public class Main {
    private static DiscordApi discordApi;

    /**
     * Initializes a Discord API connection. All listeners are enabled by default, use the remove listener method or
     * manually remove listeners in the Listener class if needed.
     */
    public static void init(){
//        Initialize the Discord Api class
        discordApi = new DiscordApiBuilder().setToken(OAuthHelper.getDiscordToken()).login().join();

//        Add a listener to the api connection, adding this also enables message responding functionality
        MessageListener messageReader = new MessageListener();
        discordApi.addListener(messageReader);

        InteractionListener interactionListener = new InteractionListener();
        discordApi.addListener(interactionListener);

//        Initialize all slash commands
//        updateSlashCommands();

//        For debugging and removing unwanted slash commands
//        List commands = discordApi.getGlobalSlashCommands().join();
    }

    /**
     * Shuts down a given listener in the case that the people who want to use it.
     * @param messageListener Listener name to shut down
     */
    public static void removeListener(MessageListener messageListener){
        discordApi.removeListener(messageListener);
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

    /**
     * Updates all slash commands when called and sends a request to create new ones if they weren't created already.
     */
    private static void updateSlashCommands(){
        slashPoll();
    }

    /**
     *  Create a "/poll" command on bot initialization
     */
    private static void slashPoll() {
         SlashCommand.with("poll", "Create a poll for members to vote on!",
                Arrays.asList(
                        SlashCommandOption.createWithOptions(SlashCommandOptionType.SUB_COMMAND, "simple", "A simple yes or no poll",
                                List.of(
                                        SlashCommandOption.create(SlashCommandOptionType.STRING, "question", "Question for the simple yes or no poll", true)
                                )
                        ),
                        SlashCommandOption.createWithOptions(SlashCommandOptionType.SUB_COMMAND, "custom", "A poll with custom voting options",
                                Arrays.asList(
                                        SlashCommandOption.create(SlashCommandOptionType.STRING, "question","Question for the poll",true),
                                        SlashCommandOption.create(SlashCommandOptionType.STRING, "1st-choice","First voting option",true),
                                        SlashCommandOption.create(SlashCommandOptionType.STRING, "2nd-choice","Second voting option",true),
                                        SlashCommandOption.create(SlashCommandOptionType.STRING, "3rd-choice","Third voting option",false),
                                        SlashCommandOption.create(SlashCommandOptionType.STRING, "4th-choice","Fourth voting option",false),
                                        SlashCommandOption.create(SlashCommandOptionType.STRING, "5th-choice","Fifth voting option",false)
                                )
                        )
                )
        ).createGlobal(discordApi).join();
    }

    /**
     * Creates a message with two emoji buttons right below. The default emojis are thumbs up and down.
     */
     static void voteMessageSimple(SlashCommandInteraction command){
//         TODO: Make the labels update with the vote count
//        Voting buttons to be placed below the message
        Button yes = Button.secondary("yes", "\uD83D\uDC4D");
        Button no = Button.secondary("no", "\uD83D\uDC4E");

         String question =
//                  Simple sub command
                 command.getFirstOption()
//                  Question parameter (Sub-command option name)
                 .get().getFirstOption()
//                  The actual question
                 .get().getStringValue().get();

        command.createImmediateResponder()
//                Question to be polled
                .setContent(question)
//                Buttons for voting
                .addComponents(ActionRow.of(yes, no))
                .respond();
    }
}
