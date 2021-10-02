package api.discord;

import org.javacord.api.entity.channel.ServerChannel;
import org.javacord.api.entity.user.User;
import org.javacord.api.event.interaction.SlashCommandCreateEvent;
import org.javacord.api.interaction.SlashCommandInteraction;
import org.javacord.api.listener.interaction.SlashCommandCreateListener;

import java.util.Optional;

public class InteractionListener implements SlashCommandCreateListener {

    @Override
    public void onSlashCommandCreate(SlashCommandCreateEvent event) {
        SlashCommandInteraction slashCommandInteraction = event.getSlashCommandInteraction();
        ServerChannel channel = slashCommandInteraction.getFirstOptionChannelValue().orElse(null);
        User user = slashCommandInteraction.getSecondOptionUserValue().orElse(null);
        Integer permissionNumber = slashCommandInteraction.getThirdOptionIntValue().orElse(null);

//        The /poll command id
        long slashPollID = 893937196615213187L;

//        If the slash command is /poll
        if(slashCommandInteraction.getCommandId() == slashPollID){
//            If the /poll was requested as simple
//            TODO: Find out what to do if this actually returns null?
            if(slashCommandInteraction.getFirstOption().orElse(null).getName().equals("simple")){
                api.discord.Main.voteMessageSimple(slashCommandInteraction);
            }
        }

    }
}
