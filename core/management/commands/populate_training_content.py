from django.core.management.base import BaseCommand
from core.models import TrainingSection, TrainingExercise


class Command(BaseCommand):
    help = 'Popula o banco de dados com conteúdo de treinamento para Guardiões'

    def handle(self, *args, **options):
        self.stdout.write('🎓 Iniciando população do conteúdo de treinamento...')
        
        # Limpar conteúdo existente
        TrainingExercise.objects.all().delete()
        TrainingSection.objects.all().delete()
        
        # Seção 1: Os Princípios do Guardião
        section1 = TrainingSection.objects.create(
            title="Os Princípios do Guardião",
            section_type="principios",
            content="""
<h3>🎯 A Filosofia do Guardião</h3>
<p>Ser um Guardião não é apenas uma função, é uma responsabilidade sagrada. Você será responsável por manter a justiça e a harmonia em nossa comunidade, tomando decisões que afetam vidas reais.</p>

<h3>📋 Regras Fundamentais</h3>

<h4>1. Imparcialidade Absoluta</h4>
<p><strong>Você é um juiz neutro.</strong> Não utilize a ferramenta para beneficiar amigos ou prejudicar desafetos. Toda análise deve ser baseada unicamente nas evidências apresentadas (mensagens).</p>

<h4>2. Zelo e Atenção</h4>
<p><strong>Cada denúncia afeta pessoas reais.</strong> Não analise casos de forma apressada ou desatenta. Leia o contexto com cuidado antes de votar.</p>

<h4>3. Honestidade no Serviço</h4>
<p><strong>O sistema de pontos recompensa sua dedicação.</strong> Ficar 'Em Serviço' sem atender ativamente às denúncias para acumular pontos é uma violação de confiança e pode levar à remoção do seu cargo.</p>

<h3>💡 Lembre-se</h3>
<p>Como Guardião, você representa os valores da comunidade. Suas decisões devem sempre refletir justiça, equidade e respeito pelos membros do servidor.</p>
            """,
            order=1
        )
        
        # Exercícios da Seção 1
        exercise1_1 = TrainingExercise.objects.create(
            section=section1,
            question="Um amigo seu foi denunciado. O que você faz?",
            option_a="Voto 'Improcedente' para ajudá-lo",
            option_b="Analiso o caso com o mesmo rigor que qualquer outro",
            option_c="Peço para ele me contar o lado dele antes de votar",
            correct_answer="b",
            explanation="A imparcialidade é fundamental. Você deve analisar TODOS os casos com o mesmo rigor, independentemente de quem seja o denunciado. Pedir informações adicionais também compromete sua neutralidade.",
            order=1
        )
        
        exercise1_2 = TrainingExercise.objects.create(
            section=section1,
            question="Você está ocupado, mas quer ganhar pontos por tempo de serviço. Qual a atitude correta?",
            option_a="Fico 'Em Serviço', mas ignoro as notificações",
            option_b="Fico 'Fora de Serviço' até poder me dedicar novamente",
            option_c="Atendo os casos rapidamente sem ler direito",
            correct_answer="b",
            explanation="A honestidade no serviço é essencial. Se você não pode se dedicar adequadamente às denúncias, deve ficar 'Fora de Serviço'. Ficar online sem atender ou atender sem cuidado são violações graves.",
            order=2
        )
        
        # Seção 2: Classificando uma Denúncia
        section2 = TrainingSection.objects.create(
            title="Classificando uma Denúncia",
            section_type="classificacao",
            content="""
<h3>⚖️ As Três Categorias de Voto</h3>
<p>Como Guardião, você deve classificar cada denúncia em uma das três categorias. Cada categoria tem critérios específicos e consequências diferentes.</p>

<h3>✅ Voto: IMPROCEDENTE</h3>
<p><strong>Quando usar:</strong> Discussões acaloradas sem ofensas diretas, brincadeiras entre usuários que não configuram assédio, denúncias falsas ou sem evidências.</p>

<p><strong>Exemplo-chave:</strong> Se dois usuários estão discutindo e ambos trocam farpas leves, punir apenas um deles é injusto. Se não houver uma violação clara, o resultado é Improcedente.</p>

<h3>⚠️ Voto: INTIMIDOU!</h3>
<p><strong>Quando usar:</strong> Xingamentos leves, ironias com intenção de ofender, provocações constantes, mensagens com duplo sentido para humilhar ou ofender. É a "zona cinzenta".</p>

<p><strong>Exemplo-chave:</strong> "Você é muito 'inteligente' pra entender isso, né?" ou "Cuidado pra não tropeçar no seu próprio ego."</p>

<h3>🚨 Voto: GRAVE</h3>
<p><strong>Quando usar:</strong> Qualquer violação clara e inequívoca das regras do Discord e da lei. Isso inclui, mas não se limita a: discurso de ódio, racismo, xenofobia, homofobia, ameaças diretas, assédio severo, compartilhamento de conteúdo explícito ou ilegal.</p>

<p><strong>Exemplo-chave:</strong> Qualquer comentário que ataque um indivíduo ou grupo com base em sua etnia, religião, orientação sexual, gênero ou deficiência.</p>

<h3>🎯 Dicas Importantes</h3>
<ul>
<li><strong>Contexto é tudo:</strong> Leia toda a conversa antes de decidir</li>
<li><strong>Intenção importa:</strong> Considere se a pessoa estava tentando ofender</li>
<li><strong>Consenso:</strong> Se é uma brincadeira entre amigos, pode ser Improcedente</li>
<li><strong>Severidade:</strong> Se há violação clara de regras, é Grave</li>
</ul>
            """,
            order=2
        )
        
        # Exercícios da Seção 2
        exercise2_1 = TrainingExercise.objects.create(
            section=section2,
            question="Log de chat: 'Usuário A: Seu argumento não faz sentido'. Usuário B: 'E você é burro'. Como classificar a mensagem do Usuário B?",
            option_a="Improcedente",
            option_b="Intimidou!",
            option_c="Grave",
            correct_answer="b",
            explanation="Chamar alguém de 'burro' é um xingamento leve com intenção de ofender. Não é grave o suficiente para ser Grave, mas também não é uma discussão normal. É um caso típico de Intimidou!",
            order=1
        )
        
        exercise2_2 = TrainingExercise.objects.create(
            section=section2,
            question="Um usuário posta um link para um site com conteúdo racista. Qual seu voto?",
            option_a="Improcedente",
            option_b="Intimidou!",
            option_c="Grave",
            correct_answer="c",
            explanation="Compartilhar conteúdo racista é uma violação clara e inequívoca das regras do Discord e da lei. Este é um caso claro de Grave, independentemente da intenção.",
            order=2
        )
        
        exercise2_3 = TrainingExercise.objects.create(
            section=section2,
            question="Dois usuários são amigos e estão se zoando com apelidos. Um terceiro usuário, de fora, denuncia. O que fazer?",
            option_a="Votar 'Intimidou!'",
            option_b="Analisar o contexto e, se for claro que é uma brincadeira consensual, votar 'Improcedente'",
            option_c="Votar 'Grave'",
            correct_answer="b",
            explanation="Contexto é fundamental. Se é uma brincadeira consensual entre amigos, não há violação. Você deve analisar toda a conversa para entender o contexto antes de decidir.",
            order=3
        )
        
        # Seção 3: Prova Final
        section3 = TrainingSection.objects.create(
            title="Prova Final",
            section_type="prova_final",
            content="""
<h3>🏆 Prova Final</h3>
<p>Esta é sua chance de demonstrar que absorveu todo o conhecimento necessário para se tornar um Guardião. A prova contém cenários realistas que você encontrará no dia a dia.</p>

<h3>📋 Regras da Prova</h3>
<ul>
<li><strong>10-15 perguntas</strong> de múltipla escolha</li>
<li><strong>Máximo 1 erro</strong> para aprovação</li>
<li><strong>2 ou mais erros</strong> = reprovação</li>
<li><strong>Reprovação:</strong> pode tentar novamente após 24 horas</li>
</ul>

<h3>🎯 Critérios de Avaliação</h3>
<p>As perguntas testam sua compreensão de:</p>
<ul>
<li>Princípios fundamentais do Guardião</li>
<li>Classificação correta de denúncias</li>
<li>Análise de contexto e intenção</li>
<li>Imparcialidade e neutralidade</li>
</ul>

<h3>💡 Dicas para Sucesso</h3>
<ul>
<li><strong>Leia com atenção:</strong> Cada palavra importa</li>
<li><strong>Analise o contexto:</strong> Considere toda a situação</li>
<li><strong>Pense como juiz:</strong> Seja imparcial e justo</li>
<li><strong>Confie no seu conhecimento:</strong> Você estudou para isso!</li>
</ul>

<h3>🚀 Boa Sorte!</h3>
<p>Se você chegou até aqui, significa que está comprometido com a missão de proteger nossa comunidade. Confie em seus conhecimentos e faça a diferença!</p>
            """,
            order=3
        )
        
        # Exercícios da Prova Final (10 perguntas)
        # Pergunta 1
        TrainingExercise.objects.create(
            section=section3,
            question="Você está analisando uma denúncia onde o usuário disse 'Você é muito burro mesmo'. O contexto mostra que foi durante uma discussão acalorada sobre política. Como classificar?",
            option_a="Improcedente - foi apenas uma discussão política",
            option_b="Intimidou! - xingamento com intenção de ofender",
            option_c="Grave - qualquer xingamento é grave",
            correct_answer="b",
            explanation="Mesmo em discussões políticas, chamar alguém de 'burro' é um xingamento com intenção de ofender. Não é grave o suficiente para ser Grave, mas também não é uma discussão normal. É Intimidou!",
            order=1
        )
        
        # Pergunta 2
        TrainingExercise.objects.create(
            section=section3,
            question="Um usuário posta uma imagem com símbolos nazistas 'apenas para mostrar o absurdo'. Como classificar?",
            option_a="Improcedente - ele estava criticando",
            option_b="Intimidou! - conteúdo ofensivo",
            option_c="Grave - símbolos nazistas são sempre graves",
            correct_answer="c",
            explanation="Símbolos nazistas são sempre graves, independentemente da intenção. Mesmo que seja para 'criticar', compartilhar esse tipo de conteúdo é uma violação clara das regras.",
            order=2
        )
        
        # Pergunta 3
        TrainingExercise.objects.create(
            section=section3,
            question="Dois amigos estão se zoando: 'Seu noob' e 'Você que é noob'. Um terceiro usuário denuncia. O que fazer?",
            option_a="Votar Intimidou! - são xingamentos",
            option_b="Votar Improcedente - é brincadeira entre amigos",
            option_c="Votar Grave - qualquer xingamento é grave",
            correct_answer="b",
            explanation="Contexto é fundamental. Se é uma brincadeira consensual entre amigos, não há violação. 'Noob' neste contexto é um termo de brincadeira, não um xingamento ofensivo.",
            order=3
        )
        
        # Pergunta 4
        TrainingExercise.objects.create(
            section=section3,
            question="Um usuário diz 'Vou te matar' durante uma partida de jogo. Como classificar?",
            option_a="Improcedente - é só um jogo",
            option_b="Intimidou! - ameaça leve",
            option_c="Grave - qualquer ameaça é grave",
            correct_answer="a",
            explanation="Contexto é crucial. Durante jogos, expressões como 'vou te matar' são comuns e não representam ameaças reais. É apenas linguagem de jogo.",
            order=4
        )
        
        # Pergunta 5
        TrainingExercise.objects.create(
            section=section3,
            question="Um usuário posta 'Todos os [grupo étnico] são iguais'. Como classificar?",
            option_a="Improcedente - é apenas uma opinião",
            option_b="Intimidou! - comentário ofensivo",
            option_c="Grave - discurso de ódio",
            correct_answer="c",
            explanation="Generalizações negativas sobre grupos étnicos constituem discurso de ódio, que é sempre Grave. Não importa se é 'apenas uma opinião' - isso viola regras fundamentais.",
            order=5
        )
        
        # Pergunta 6
        TrainingExercise.objects.create(
            section=section3,
            question="Um usuário diz 'Você é muito inteligente pra entender isso' de forma sarcástica. Como classificar?",
            option_a="Improcedente - é um elogio",
            option_b="Intimidou! - sarcasmo com intenção de ofender",
            option_c="Grave - sarcasmo é sempre grave",
            correct_answer="b",
            explanation="Sarcasmo com intenção de ofender é um caso típico de Intimidou!. A pessoa está sendo irônica para humilhar, mas não é grave o suficiente para ser Grave.",
            order=6
        )
        
        # Pergunta 7
        TrainingExercise.objects.create(
            section=section3,
            question="Um usuário posta conteúdo pornográfico 'para zoar'. Como classificar?",
            option_a="Improcedente - era só uma brincadeira",
            option_b="Intimidou! - conteúdo inadequado",
            option_c="Grave - conteúdo explícito é sempre grave",
            correct_answer="c",
            explanation="Conteúdo pornográfico é sempre Grave, independentemente da intenção. Servidores Discord têm regras claras sobre conteúdo explícito.",
            order=7
        )
        
        # Pergunta 8
        TrainingExercise.objects.create(
            section=section3,
            question="Um usuário diz 'Você é muito chato' durante uma discussão. Como classificar?",
            option_a="Improcedente - é apenas uma crítica",
            option_b="Intimidou! - comentário ofensivo",
            option_c="Grave - qualquer crítica é grave",
            correct_answer="a",
            explanation="'Chato' é uma crítica leve, não um xingamento ofensivo. Durante discussões, é normal expressar descontentamento. Não há violação clara aqui.",
            order=8
        )
        
        # Pergunta 9
        TrainingExercise.objects.create(
            section=section3,
            question="Um usuário posta 'Kill yourself' para outro usuário. Como classificar?",
            option_a="Improcedente - é só uma expressão",
            option_b="Intimidou! - comentário ofensivo",
            option_c="Grave - incentivo à autoagressão",
            correct_answer="c",
            explanation="'Kill yourself' é um incentivo direto à autoagressão, que é sempre Grave. Mesmo que seja 'só uma expressão', isso pode ter consequências sérias.",
            order=9
        )
        
        # Pergunta 10
        TrainingExercise.objects.create(
            section=section3,
            question="Um usuário diz 'Você é muito burro mesmo, não consegue entender nada' repetidamente. Como classificar?",
            option_a="Improcedente - é só uma crítica",
            option_b="Intimidou! - provocações constantes",
            option_c="Grave - qualquer repetição é grave",
            correct_answer="b",
            explanation="Provocações constantes e repetitivas constituem assédio leve. Não é grave o suficiente para ser Grave, mas também não é uma crítica normal. É Intimidou!",
            order=10
        )
        
        # Pergunta 11
        TrainingExercise.objects.create(
            section=section3,
            question="Um usuário posta 'Todos os gays são doentes mentais'. Como classificar?",
            option_a="Improcedente - é apenas uma opinião",
            option_b="Intimidou! - comentário ofensivo",
            option_c="Grave - homofobia é sempre grave",
            correct_answer="c",
            explanation="Homofobia é sempre Grave. Qualquer ataque baseado em orientação sexual constitui discurso de ódio e viola regras fundamentais.",
            order=11
        )
        
        # Pergunta 12
        TrainingExercise.objects.create(
            section=section3,
            question="Um usuário diz 'Você é muito burro' uma vez durante uma discussão acalorada. Como classificar?",
            option_a="Improcedente - foi só uma discussão",
            option_b="Intimidou! - xingamento com intenção de ofender",
            option_c="Grave - qualquer xingamento é grave",
            correct_answer="b",
            explanation="Chamar alguém de 'burro' é um xingamento com intenção de ofender. Mesmo em discussões acaloradas, isso não é uma discussão normal. É Intimidou!",
            order=12
        )
        
        # Pergunta 13
        TrainingExercise.objects.create(
            section=section3,
            question="Um usuário posta 'Vou te encontrar e te ensinar uma lição'. Como classificar?",
            option_a="Improcedente - é só uma expressão",
            option_b="Intimidou! - ameaça leve",
            option_c="Grave - ameaça direta",
            correct_answer="c",
            explanation="'Vou te encontrar e te ensinar uma lição' é uma ameaça direta de violência física. Ameaças diretas são sempre Graves.",
            order=13
        )
        
        # Pergunta 14
        TrainingExercise.objects.create(
            section=section3,
            question="Um usuário diz 'Você é muito inteligente' de forma genuína. Como classificar?",
            option_a="Improcedente - é um elogio",
            option_b="Intimidou! - pode ser sarcasmo",
            option_c="Grave - elogios são sempre graves",
            correct_answer="a",
            explanation="Elogios genuínos não constituem violação. Se não há intenção de ofender ou violar regras, é Improcedente.",
            order=14
        )
        
        # Pergunta 15
        TrainingExercise.objects.create(
            section=section3,
            question="Um usuário posta 'Você é muito burro mesmo, não consegue entender nada' e depois 'Desculpa, foi só uma brincadeira'. Como classificar?",
            option_a="Improcedente - ele se desculpou",
            option_b="Intimidou! - xingamento com intenção de ofender",
            option_c="Grave - desculpa não muda a violação",
            correct_answer="b",
            explanation="Desculpas não apagam a violação original. O usuário ainda xingou com intenção de ofender. A desculpa pode ser considerada no contexto, mas não elimina a violação.",
            order=15
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Conteúdo de treinamento criado com sucesso!\n'
                f'📚 Seções: {TrainingSection.objects.count()}\n'
                f'❓ Exercícios: {TrainingExercise.objects.count()}\n'
                f'🎯 Pronto para uso!'
            )
        )
