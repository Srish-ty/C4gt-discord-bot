import asyncio
import json
import os
import sys
from typing import Union

import aiohttp
import discord
import dotenv
from discord.ext import commands

from helpers.supabaseClient import SupabaseClient

# Since there are user defined packages, adding current directory to python path
current_directory = os.getcwd()
sys.path.append(current_directory)

dotenv.load_dotenv(".env")


# class GithubAuthModal(discord.ui.Modal):
# def __init__(self, *,userID, title: str = None, timeout: float | None = None, custom_id: str = None) -> None:
#     super().__init__(title=title, timeout=timeout, custom_id=custom_id)
#     self.add_item(discord.ui.Button(label='Authenticate Github', style=discord.ButtonStyle.url, url=f'https://github-app.c4gt.samagra.io/authenticate/{userID}'))
class AuthenticationView(discord.ui.View):
    def __init__(self, discord_userdata):
        super().__init__()
        button = discord.ui.Button(
            label="Authenticate Github",
            style=discord.ButtonStyle.url,
            url=f"https://github-app.c4gt.samagra.io/authenticate/{discord_userdata}",
        )
        self.add_item(button)
        self.message = None


# class ChapterSelect(discord.ui.Select):
#     def __init__(self, affiliation, data):
#         collegeOptions = [discord.SelectOption(label=option["label"], emoji=option["emoji"] ) for option in [
#             {
#                 "label": "NIT Kurukshetra",
#                 "emoji": "\N{GRADUATION CAP}"
#             },
#             {
#                 "label": "ITER, Siksha 'O' Anusandhan",
#                 "emoji": "\N{GRADUATION CAP}"
#             },
#             {
#                 "label": "IIITDM Jabalpur",
#                 "emoji": "\N{GRADUATION CAP}"
#             },
#             {
#                 "label": "KIIT, Bhubaneswar",
#                 "emoji": "\N{GRADUATION CAP}"
#             }

#         ]]
#         corporateOptions = []
#         self.data = data
#         super().__init__(placeholder="Please select your institute",max_values=1,min_values=1,options=collegeOptions if affiliation=="College Chapter" else corporateOptions)
#     async def callback(self, interaction:discord.Interaction):
#         self.data["chapter"] = self.values[0]
#         self.data["discord_id"]= interaction.user.id

#         await interaction.response.send_message("Now please Authenticate using Github so we can start awarding your points!",view=AuthenticationView(interaction.user.id), ephemeral=True)

# class AffiliationSelect(discord.ui.Select):
#     def __init__(self, data):
#         options = [discord.SelectOption(label=option["label"], emoji=option["emoji"] ) for option in [
#             {
#                 "label": "College Chapter",
#                 "emoji": "\N{OPEN BOOK}"
#             },
#             {
#                 "label": "Corporate Chapter",
#                 "emoji": "\N{OFFICE BUILDING}"
#             },
#             {
#                 "label": "Individual Contributor",
#                 "emoji": "\N{BRIEFCASE}"
#             }
#         ]]
#         super().__init__(placeholder="Please select applicable affliliation",max_values=1,min_values=1,options=options)
#         self.data = data
#     async def callback(self, interaction:discord.Interaction):
#         self.data["affiliation"] = self.values[0]
#         if self.values[0] == "College Chapter":
#             chapterView = discord.ui.View()
#             chapterView.add_item(ChapterSelect(self.values[0], self.data))
#             await interaction.response.send_message("Please select your institute!", view=chapterView, ephemeral=True)
#         elif self.values[0] == "Corporate Chapter":
#             await interaction.response.send_message("We currently don't have any active Corporate Chapters!", ephemeral=True)
#         elif self.values[0] == "Individual Contributor":
#             await interaction.response.send_message("Now please Authenticate using Github so we can start awarding your points!",view=AuthenticationView(interaction.user.id), ephemeral=True)

# class AffiliationView(discord.ui.View):
# def __init__(self, data):
#     super().__init__()
#     self.timeout = None
#     self.add_item(AffiliationSelect(data))


class RegistrationModal(discord.ui.Modal):
    def __init__(
        self,
        *,
        title: str = None,
        timeout: Union[float, None] = None,
        custom_id: str = None,
    ) -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)

    async def post_data(self, data):
        url = "https://kcavhjwafgtoqkqbbqrd.supabase.co/rest/v1/contributor_names"
        headers = {
            "apikey": f"{os.getenv('SUPABASE_KEY')}",
            "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, headers=headers, data=json.dumps(data)
            ) as response:
                if response.status == 200:
                    print("Data posted successfully")
                else:
                    print("Failed to post data")
                    print("Status Code:", response.status)

    name = discord.ui.TextInput(
        label="Please Enter Your Name",
        placeholder="To give you the recognition you deserve, could you please share your full name for the certificates!",
    )

    async def on_submit(self, interaction: discord.Interaction):
        user = interaction.user
        await interaction.response.send_message(
            "Thanks! Now please sign in via Github!",
            view=AuthenticationView(user.id),
            ephemeral=True,
        )
        await self.post_data({"name": self.name.value, "discord_id": user.id})

        verifiedContributorRoleID = 1123967402175119482
        print("User:", type(user))
        if verifiedContributorRoleID in [role.id for role in user.roles]:
            return
        else:

            async def hasIntroduced():
                print("Checking...")
                authentication = SupabaseClient().read(
                    "contributors_registration", "discord_id", user.id
                )
                while not authentication:
                    await asyncio.sleep(30)
                print("Found!")
                discordEngagement = SupabaseClient().read(
                    "discord_engagement", "contributor", user.id
                )[0]
                return discordEngagement["has_introduced"]

            try:
                await asyncio.wait_for(hasIntroduced(), timeout=1000)
                verifiedContributorRole = user.guild.get_role(verifiedContributorRoleID)
                if verifiedContributorRole:
                    if verifiedContributorRole not in user.roles:
                        await user.add_roles(
                            verifiedContributorRole,
                            reason="Completed Auth and Introduction",
                        )
            except asyncio.TimeoutError:
                print("Timed out waiting for authentication")


class RegistrationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Register",
        style=discord.enums.ButtonStyle.blurple,
        custom_id="registration_view:blurple",
    )
    async def reg(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RegistrationModal(
            title="Contributor Registration", custom_id="registration:modal"
        )
        await interaction.response.send_modal(modal)


class C4GTBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        intents.message_content = True

        super().__init__(
            command_prefix=commands.when_mentioned_or("!"), intents=intents
        )

    async def setup_hook(self) -> None:
        # Register the persistent view for listening here.
        # Note that this does not send the view to any message.
        # In order to do this you need to first send a message with the View, which is shown below.
        # If you have the message_id you can also pass it as a keyword argument, but for this example
        # we don't have one.
        self.add_view(RegistrationView())


client = C4GTBot()


@client.command(aliases=["registration"])
async def registerAsContributor(ctx, channel: discord.TextChannel):
    # guild = ctx.guild
    # channelID = 1167054801385820240
    # channel = guild.get_channel_or_thread(channelID)
    await channel.send(
        "Please register using Github to sign up as a C4GT Contributor",
        view=RegistrationView(),
    )


# alert message on commandline that bot has successfully logged in


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


# load cogs
async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await client.load_extension(f"cogs.{filename[:-3]}")

    # ### All listener cogs
    for filename in os.listdir("./cogs/listeners"):
        if filename.endswith("cog.py"):
            await client.load_extension(f"cogs.listeners.{filename[:-3]}")


async def main():
    async with client:
        await load()
        await client.start(os.getenv("TOKEN"))


asyncio.run(main())
