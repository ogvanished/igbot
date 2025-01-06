import nextcord
from nextcord.ext import commands
from nextcord.ui import Button, View

TOKEN = 'MTMyNDQ0NjI3Mzc4ODU3OTk0MQ.GyXNCR.hAlTUOvS4O1xBhRUynV-0SQipYnz9M276oeqP8'  # Substitua pelo token do bot
intents = nextcord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix=',', intents=intents)  # Prefixo atualizado para ','

# Dicionário para armazenar posts e seus comentários
posts = {}

@bot.event
async def on_ready():
    print(f'{bot.user} está online!')

class PostView(View):
    def __init__(self, post_message, post_id):
        super().__init__(timeout=None)  # Sem limite de tempo para os botões
        self.post_message = post_message
        self.post_id = post_id

    @nextcord.ui.button(label="Curtir", style=nextcord.ButtonStyle.green)
    async def like_button(self, button: Button, interaction: nextcord.Interaction):
        """Gerencia a interação do botão de curtir."""
        post = posts[self.post_id]

        # Verifica se o usuário já curtiu o post
        if interaction.user.display_name in post["likes_users"]:
            await interaction.response.send_message("Você já curtiu este post!", ephemeral=True)
            return

        # Adiciona o usuário à lista de curtidas
        post["likes_users"].append(interaction.user.display_name)
        post["likes"] += 1
        await interaction.response.send_message(f"Você curtiu o post! ❤️ Total de curtidas: {post['likes']}", ephemeral=True)

    @nextcord.ui.button(label="Ver Curtidas", style=nextcord.ButtonStyle.primary)
    async def view_likes_button(self, button: Button, interaction: nextcord.Interaction):
        """Gerencia a interação do botão de visualizar curtidas."""
        post = posts[self.post_id]
        if post["likes_users"]:
            liked_by = "\n".join(post["likes_users"])
            await interaction.response.send_message(f"Usuários que curtiram este post:\n{liked_by}", ephemeral=True)
        else:
            await interaction.response.send_message("Ninguém curtiu este post ainda.", ephemeral=True)

    @nextcord.ui.button(label="Comentar", style=nextcord.ButtonStyle.primary)
    async def comment_button(self, button: Button, interaction: nextcord.Interaction):
        """Gerencia a interação do botão de comentar."""
        post = posts[self.post_id]

        # Verifica se o usuário já comentou
        if any(comment[0] == interaction.user.display_name for comment in post["comments"]):
            await interaction.response.send_message("Você já comentou este post!", ephemeral=True)
            return

        # Envia uma mensagem no PV pedindo o comentário
        try:
            dm_channel = await interaction.user.create_dm()
            await dm_channel.send("Digite seu comentário para o post:")
        except Exception:
            await interaction.response.send_message("Não consegui enviar uma mensagem no seu PV. Verifique suas configurações.", ephemeral=True)
            return

        def check(m):
            return m.author == interaction.user and m.channel == dm_channel

        try:
            comment_message = await bot.wait_for('message', check=check, timeout=60.0)
            post["comments"].append((interaction.user.display_name, comment_message.content))
            await dm_channel.send("Seu comentário foi adicionado com sucesso!")
            await interaction.response.send_message("Seu comentário foi registrado com sucesso!", ephemeral=True)
        except TimeoutError:
            await dm_channel.send("Você demorou muito para responder. Tente novamente.")
            await interaction.response.send_message("Você não respondeu a tempo. Tente novamente.", ephemeral=True)

    @nextcord.ui.button(label="Ver Comentários", style=nextcord.ButtonStyle.grey)
    async def view_comments_button(self, button: Button, interaction: nextcord.Interaction):
        """Gerencia a interação do botão de visualizar comentários."""
        post = posts[self.post_id]
        if post["comments"]:
            comments_text = "\n".join([f"**{author}**: {comment}" for author, comment in post["comments"]])
            await interaction.response.send_message(f"Comentários:\n{comments_text}", ephemeral=True)
        else:
            await interaction.response.send_message("Ainda não há comentários.", ephemeral=True)


@bot.command(name='postar')  # Comando renomeado para "postar"
async def postar(ctx, *, caption=None):
    """Comando para criar um post com uma legenda opcional."""
    if not ctx.message.attachments:
        await ctx.send("Por favor, anexe uma imagem ao seu post!")
        return

    image_url = ctx.message.attachments[0].url

    embed = nextcord.Embed(title="Novo Post!", description=caption or "", color=0x000000)  # Cor preta (#000000)
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
    embed.set_image(url=image_url)
    embed.set_footer(text="Use os botões abaixo para interagir com o post!")

    post_message = await ctx.send(embed=embed)

    # Cria a estrutura de dados do post
    post_id = post_message.id
    posts[post_id] = {
        "author": ctx.author,
        "caption": caption,
        "image_url": image_url,
        "likes": 0,
        "likes_users": [],
        "comments": []
    }

    # Cria a view (com botões) para o post
    view = PostView(post_message, post_id)
    await post_message.edit(view=view)

    # Apaga a mensagem original enviada pelo usuário
    await ctx.message.delete()

bot.run(TOKEN)
