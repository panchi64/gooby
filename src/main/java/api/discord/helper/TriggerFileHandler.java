package api.discord.helper;

import api.discord.Main;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.Map;
import java.util.Scanner;
import java.util.Set;
import java.util.TreeMap;

public class TriggerFileHandler {
  private static final Logger logger = LoggerFactory.getLogger(Main.class);

  public static Map<String, String[]> generateMap(String path) throws FileNotFoundException {
    Scanner scanner = new Scanner(new FileReader(path));
    Map<String, String[]> triggerMap = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
    String line;

    while (scanner.hasNext()) {
      line = scanner.nextLine();

      String[] keyValuePair = line.split("=");
      String[] responses = keyValuePair[1].split("~~");
      triggerMap.put(keyValuePair[0], responses);
    }

    return triggerMap;
  }

  /**
   * Writes a map to a file.
   *
   * @param triggerMap Map to be written to file.
   * @param path       Path to file.
   */
  public static void saveTriggersToFile(Map<String, String[]> triggerMap, String path) {
    Set<String> triggerSet = triggerMap.keySet();
    for (String triggerKey : triggerSet) {
      String[] response = triggerMap.get(triggerKey);

      try (FileWriter file = new FileWriter(path)) {
        file.write(triggerKey + "=" + String.join(" ~~ ", response));
      } catch (IOException ioException) {
        logger.error("System has failed in saving the triggers to the given file path.", ioException);
      }
    }
  }
}
