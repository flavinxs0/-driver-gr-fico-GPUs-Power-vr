# Análise DragonBurst — 2026-11-05

## Identificação

- Pacote: `DragonBurst-logs-20261105-104022.zip`
- SHA-256: `823ad827fbfd33b37777b12dd79ac25f5342ced05fca08d4b439308d685f13cd`
- Dispositivo: Motorola moto g73 5G (`devonf`)
- SoC/board: MediaTek `MT6855V/AZA` / `mt6855`
- Android: 14 / API 34
- App: Dragon Burst `0.2.1 (5)`
- Arquivos do jogo: `default.xex`, `LONG2DATA` e demais dados reportados como OK

## Causa do encerramento

A falha é um encerramento intencional do launcher/engine, não um crash nativo do Mesa PVR:

```text
Renut: driver Vulkan do sistema
Renut: PowerVR BXM-8-256 (Vulkan 1.1)
Renut: o driver nao tem bufferDeviceAddress descriptorIndexing 8192-texturas 5-descriptor-sets
Renut: o driver nao tem o que o Renut precisa (...); o jogo fecha (o launcher diz porque)
```

O driver usado foi explicitamente o driver Vulkan do sistema. O log não mostra carregamento da `libvulkan_powervr_mesa.so` nem de uma camada Mesa personalizada. Portanto, este teste ainda não valida o driver Mesa PVR em desenvolvimento.

## Capacidades observadas pelo jogo

- GPU identificada: PowerVR BXM-8-256.
- Vulkan: 1.1.
- `maxBoundDescriptorSets`: 4.
- `maxPushConstantsSize`: 128.
- `maxPerStageDescriptorUpdateAfterBindSampledImages`: 0.
- `maxPerStageUpdateAfterBindResources`: 0.
- Texturas BC: ausentes; o engine ativou descompressão durante upload.
- O engine exige, no mínimo, `bufferDeviceAddress`, `descriptorIndexing`, 8192 texturas e 5 descriptor sets.

A diferença direta é `maxBoundDescriptorSets=4` contra a exigência de 5. O log também indica ausência de `bufferDeviceAddress` e `descriptorIndexing`, que por si só já dispara o encerramento.

## Avisos não fatais

- `avc: denied { execstack }` para `libgame.so`: o Android bloqueou uma stack executável. A biblioteca ainda foi carregada e o SDL chegou a iniciar; pode causar falhas posteriores, mas não é a causa do encerramento observado.
- `Attempt to load writable file ... libgame.so`: aviso de compatibilidade futura do Android; não interrompeu esta execução.
- `libmagtsync.so` ausente: aparece no componente FBI, mas o jogo prosseguiu até a checagem Vulkan.
- `OpenGLRenderer: Unable to match the desired swap behavior`: aviso de apresentação do launcher/superfície, não a causa do fechamento.
- `Adreno: false` e `Turnip UNSUPPORTED kgsl=false`: são heurísticas corretas para descartar Turnip/Adreno, embora a mensagem `Adreno ?` seja apenas uma representação incompleta do app.

## Relação com o Mesa PVR

Este log confirma que o aparelho/engine é o alvo correto do projeto Mesa PVR: MT6855, PowerVR BXM-8-256 e Vulkan. Porém, o teste foi executado com o driver proprietário do sistema. Antes de concluir que o Mesa não funciona, é necessário carregar o ICD Mesa de forma controlada e repetir a coleta de `VkPhysicalDeviceFeatures2` e `VkPhysicalDeviceProperties`.

Mesmo com o Mesa carregado, não é correto simplesmente anunciar recursos ausentes. Para o Renut iniciar, o driver precisaria implementar corretamente `bufferDeviceAddress`, `descriptorIndexing`, pelo menos 5 descriptor sets e o conjunto de limites exigido. Se o hardware/firmware ou o backend PVR não suportarem esses recursos, o comportamento seguro é reportar a limitação e manter o encerramento, não forçar os bits Vulkan.

## Próximas ações técnicas

1. Confirmar pelo log do app qual ICD foi selecionado, incluindo caminho e nome da biblioteca.
2. Testar o Mesa PVR com um pequeno probe Vulkan antes do jogo, registrando extensões, features e limites.
3. Corrigir primeiro o carregamento/seleção do ICD; este log mostra que o Mesa ainda não foi selecionado.
4. Depois, comparar os recursos reportados pelo Mesa com a lista exigida pelo Renut.
5. Tratar `execstack` em `libgame.so` separadamente, removendo a dependência de stack executável se o jogo falhar depois de passar da checagem Vulkan.

## Conclusão

O encerramento observado é esperado pelo código do DragonBurst: o driver Vulkan de sistema foi selecionado, mas não fornece os recursos mínimos exigidos pelo Renut. Não há evidência neste pacote de crash do Mesa PVR, de corrupção do `default.xex` ou de ausência dos arquivos do jogo.
