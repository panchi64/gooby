# Gooby - The Discord Bot
This is a Discord bot built with Rust. It's designed for private server use and comes with various entertaining and useful features to enhance your server experience. From creating polls and playing music to generating AI images and custom memes, Gooby has got you covered!

## Features
- **Polls**: Easily create polls for your server members to vote on.
- **Music Playback**: Play music in voice channels to keep your server lively and entertaining.
- **Dice Rolling**: Roll virtual dice for gaming sessions or random decision-making.
- **AI Image Generation**: Generate unique and creative images using advanced AI technology.
- **Random User Mocking**: Add a touch of humor by randomly mocking users in a friendly manner.
- **Server Report Management**: Efficiently manage and track server reports for moderation purposes.
- **Custom Meme Generation**: Create personalized memes by editing the text on popular meme templates.
  
## Installation
#### Clone the repository:

`git clone https://github.com/yourusername/discord-bot.git`

#### Install Rust:
   
Follow the official installation guide at https://www.rust-lang.org/tools/install

#### Build the project:

```
cd discord-bot
cargo build --release
```

#### Configure the bot:

Open the `config.toml` file and enter your Discord bot token and other necessary settings.

#### Run the bot:

`./target/release/discord-bot`

## Usage

1. Invite the bot to your Discord server using the invite link.
2. Use the following commands to interact with the bot:
- `/poll`: Create a new poll with a question and options.
- `/play`: Play music in a voice channel.
- `/roll`: Roll dice with a specified number of sides.
- `/generate`: Generate an AI image based on a given prompt.
- `/mock`: Enable mocking a user humorously.
- `/report`: Manage and view server reports.
- `/meme`: Generate a custom meme by providing the meme template and text.
3. Enjoy the bot's features and have fun with your server members!

## Contributing

Contributions are welcome! 
If you have any ideas, suggestions, or bug reports, please open an [issue](https://github.com/panchi64/gooby/issues) or submit a [pull request](https://github.com/panchi64/gooby/pulls). 
Make sure to follow the project's code of conduct.

## License
This project is licensed under the GNU General Public License v3.0

## Dependencies
- Serenity - A Rust library for the Discord API.
- Songbird - A Rust library for the Discord voice API.
- Image - A Rust library for image processing.
- Rust-OpenAI - A Rust library for interacting with the OpenAI API.

## Contact
For any questions or inquiries, please create an [issue](https://github.com/panchi64/gooby/issues). I'll take a look at it and respond accordingly.
