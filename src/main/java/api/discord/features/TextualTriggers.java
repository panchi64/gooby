package api.discord.features;

import discord4j.core.event.domain.message.MessageCreateEvent;
import discord4j.core.object.entity.Message;
import reactor.core.publisher.Mono;

import java.util.Map;

public class TextualTriggers {
    private Map<String, String> triggers;

    /**
     * Sets the HashMap for the class.
     *
     * @param triggerMap HashMap containing the Key|Value pairs desired to be searched for in messages.
     */
    public void setTriggers(Map<String, String> triggerMap) {
        this.triggers = triggerMap;
    }

    /**
     * @return Class Map containing the Key|Value pairs to be searched for in messages given to it.
     */
    public Map<String, String> getTriggers() {
        return this.triggers;
    }

    /**
     * Responds to a message if the message contains a trigger word found in the given Map.
     *
     * @param triggerMap Map containing the bots text triggers.
     * @param event      Message received.
     * @return Message in the given channel.
     */
    public Mono<Object> respond(Map<String, String> triggerMap, MessageCreateEvent event) {
        Message message = event.getMessage();
        String messageContent = message.getContent();

//        Compares string to every key and checks if the string contains a trigger as some sort of substring.
        for (String key : triggerMap.keySet()) {
            if (messageContent.contains(key)) {
                return message.getChannel().flatMap(channel -> channel.createMessage(triggerMap.get(key)));
            }
        }

        return Mono.empty();
    }
}
