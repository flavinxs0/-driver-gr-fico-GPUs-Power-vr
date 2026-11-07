# Análise dos relatórios PVR — Moto G54 / MT6855 — 2026-11-07

## Escopo e limite das fontes

O arquivo recebido `Download.zip` contém dois PDFs: `Relatorio_Completo_PowerVR_Moto_G54_2026-11-06.pdf` e `relatorio_pvr_gpu_mt6855_parte2.pdf`. Não contém os logs brutos nem o ZIP de coleta mencionado no segundo relatório; os valores abaixo são, portanto, uma análise dos relatórios, não uma revalidação independente dos dados originais.

Os documentos descrevem um Moto G54 (plataforma MT6855, Android 15). Não são um novo teste do Moto G73 nem do Moto G56 e não devem ser tratados como se fossem o log do DMC4 no G73.

## O que os relatórios sustentam

O relatório completo identifica, pelo Vulkan do sistema, uma PowerVR BXM-8-256 integrada no MT6855. A pilha proprietária reporta vendor ID `0x1010`, device ID `0x35010101`, driver info `1.15@6133110` e API do dispositivo `1.1.170`. A versão `1.3.368` mencionada no documento é a versão da instância/loader, não a versão anunciada pelo dispositivo físico.

Há uma correspondência útil: a patch 0003 do repositório corrigiu o device ID Mesa provisório de `0x35408101` para `0x35010101`, igual ao valor reportado pelo driver proprietário. Isso remove uma divergência conhecida do ID, mas não prova que o Mesa inicialize nem que o DMC4 enumere esse dispositivo.

O mesmo relatório descreve extensões e features do driver proprietário, incluindo descriptor indexing, buffer device address e compressão ASTC/ETC2/PVRTC, além de `maxBoundDescriptorSets = 4` e `maxPushConstantsSize = 128`. Esses valores são do driver proprietário consultado por `vulkaninfo`; eles não comprovam que o Mesa experimental anuncie as mesmas extensões, recursos ou limites. Em particular, não se deve copiar a lista de capabilities do vendor para justificar uma alteração de features no Mesa.

A Parte 2 informa Android 15, kernel 5.10.240 e `init.svc.gpu=running`. O módulo, firmware e bibliotecas pertencem à família Rogue DDK 1.15; as bibliotecas de usuário reportam `1.15@6133110`, coerente com a versão que o projeto Mesa está configurando. O rótulo de árvore/build `m1.15RTM26133109_TD` difere do build reportado pelas bibliotecas, mas o próprio relatório observa que isso pode ser apenas uma identificação de árvore. Os dados não demonstram, por si, que o handshake do Mesa experimental já funcionou.

## O que o teste sob carga não mede

As 90 amostras de `top` são métricas de CPU, não de GPU. Durante o AIO Graphics Test por Wine/DXVK, o relatório estima cerca de 543% de uso agregado em usuário+sistema+IRQ num aparelho de oito núcleos; `dxvk-submit`, `dxvk-cs` e `dxvk-queue` aparecem entre as threads mais ocupadas. Isso sugere custo alto de tradução/submissão na CPU, mas não prova que a GPU esteja saturada nem permite inferir FPS ou estabilidade do driver.

A memória livre reportada (144–443 MB), swap em uso (aprox. 2,0–2,12 GB) e pico de `kcompactd0` a 64% indicam pressão de memória durante parte do teste. Antes de uma nova medição, convém fechar apps em segundo plano e executar somente um teste gráfico; a pressão de memória pode contaminar comparações de desempenho e aumentar o risco de encerramento por falta de memória.

Não há amostras de frequência nem utilização da GPU sob carga. O valor isolado de 390 MHz / aproximadamente 7% citado da Parte 1 é um instantâneo em repouso, não uma medida durante o AIO. `custom_boost_gpu_freq=23` não pode ser convertido em MHz sem a tabela de OPPs, e não há base nesses PDFs para alterar limites de DVFS.

A página 3 do segundo PDF corta o comando de leitura no fim da linha (inclui apenas parte do caminho de utilização). Não copie aquele comando como está. Primeiro identifique os nomes exatos dos nós de leitura em `/sys/kernel/ged/hal` com acesso autorizado; depois valide a leitura de frequência/utilização antes de montar o loop. Não escreva nesses nós nem altere parâmetros de DVFS.

## Relação com a falha “no Vulkan device”

Esses PDFs caracterizam o driver proprietário do Moto G54 e uma carga AIO/DXVK. Não registram o carregamento do `libvulkan_powervr_mesa.so` dentro do DMC4, a contagem de `vkEnumeratePhysicalDevices` desse jogo, as propriedades retornadas pelo Mesa nem `vkCreateDevice`. Portanto, não resolvem a falha do DMC4 no Moto G73 nem confirmam que o Mesa experimental já expõe uma GPU.

O relatório fortalece a escolha de alvo MT6855/DDK 1.15 e oferece uma referência proprietária para comparar nomes/IDs/API. A patch 0006 do projeto alinha a versão cliente para DDK 1.15/build `6133110`; a patch 0007 foi preparada para registrar, na inicialização normal do Mesa, descoberta DRM, acesso ao render node, handshake/bridge, BVNC, propriedades Vulkan calculadas e publicação do dispositivo. Os dados do novo teste devem ser interpretados pelos logs `PVR_DIAG`, sem presumir que a pilha proprietária e a Mesa tenham as mesmas capabilities.

## Próximo teste útil

Após o workflow Android concluir com sucesso, teste o pacote principal no Moto G54 e selecione explicitamente o ICD Mesa no wrapper. Reproduza a inicialização do renderer e capture o logcat sem limpá-lo; procure as linhas `PVR_DIAG` e a mensagem final do DMC4. Se o Mesa publicar um dispositivo e o jogo ainda disser “no Vulkan device”, a investigação passa às propriedades/capabilities que o jogo filtra. Se falhar antes de publicar, os logs devem distinguir ausência/inacessibilidade do nó DRM, rejeição do driver, falha DDK ou BVNC não suportado.

Não use neste passo root para forçar o carregamento, substituir o driver do sistema ou escrever em parâmetros do GED. O teste de frequência é separado do diagnóstico da enumeração Vulkan.
