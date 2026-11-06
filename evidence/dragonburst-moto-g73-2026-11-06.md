# Diagnóstico DragonBurst — Moto G73 — 2026-11-06

## Evidência analisada

Pacote: `WhatsAppDocuments.zip`, com `DragonBurst-logs-20261106-131122.zip` e `DragonBurst-logs-20261106-132800.zip`.

O inventário dos dois pacotes identifica `motorola moto g73 5G (devonf)`, Android 14/API 34, MediaTek MT6855V/AZA, placa `mt6855`, e driver PowerVR BXM-8-256. A configuração declara um driver custom selecionado; isso, isoladamente, não prova que a biblioteca foi efetivamente inicializada naquela sessão.

## Execução de 13:11 — tentativa Mesa

O aparelho declara `vulkan_pvr_bxm8256_adrenotools` como selecionado. O logcat registra que a biblioteca Mesa (`libvulkan_powervr_mesa.so`, 12.134.352 bytes) encerrou o jogo na inicialização anterior; o launcher então escolheu o driver do sistema. O runtime da sessão em questão também escreve `Renut: driver Vulkan do sistema`.

O driver de fábrica enumera uma `PowerVR BXM-8-256` e o jogo encerra porque faltam `bufferDeviceAddress`, `descriptorIndexing`, 8192 texturas e 5 descriptor sets. Essa rejeição caracteriza o driver do sistema, após fallback. Não é a mensagem de erro do Mesa e não prova que o Mesa chegou a enumerar uma GPU.

A causa original do encerramento Mesa não está preservada nos arquivos deste ZIP. Portanto, ainda não é possível concluir se foi falha de dependência ELF, falha de inicialização Android, abertura/acesso ao render node, negociação DDK/bridge, ou outro crash.

## Execução de 13:28 — tentativa wrapper

O inventário seleciona `vulkan_pvr_adrenotools`. O hook tenta carregar `libvulkan_wrapper.so`, mas o linker reporta:

```text
failed to load custom driver: dlopen failed: library "libadrenotools.so" not found: needed by .../driver/libvulkan_wrapper.so in namespace vulkan.mtk.so!
```

O hook cai explicitamente de volta ao sistema. O renderer volta a identificar o PowerVR proprietário e o DragonBurst repete a rejeição de recursos. Isso é um erro de empacotamento/visibilidade de dependência do wrapper, não um teste do Mesa PVR.

## O que os logs permitem afirmar

1. O hardware reportado no Moto G73 é o alvo BXM-8-256/MT6855.
2. A pilha de fábrica consegue enumerar a GPU, mas não satisfaz os requisitos Vulkan do renderer Renut.
3. A tentativa com o wrapper não passou de `dlopen`; falta tornar `libadrenotools.so` visível no linker namespace, junto de suas dependências, ou eliminar essa camada.
4. Uma tentativa Mesa anterior encerrou o jogo. Os logs fornecidos não contêm o erro raiz dessa inicialização. As execuções observadas usaram o driver de sistema após fallback.
5. Não se deve anunciar bits de `bufferDeviceAddress` ou descriptor indexing, elevar limites nem falsificar IDs para passar a checagem. Isso violaria os contratos Vulkan e poderia converter uma falha clara em corrupção ou travamento posterior.

## Correções e critério de teste

- Para o pacote wrapper: corrigir a integração no app/namespace para que `libadrenotools.so` e todas as dependências transitivas estejam resolvíveis pelo linker Android no namespace `vulkan.mtk.so`. Copiar a biblioteca para um ZIP sem garantir que o namespace pesquise o diretório não é uma correção suficiente.
- Para o Mesa direto: recolher o log da mesma execução em que ele falha, sem deixar o fallback ocultar o primeiro erro. A coleta precisa incluir `linker`, `libc`, `AndroidRuntime`, SELinux AVCs, mensagens Vulkan do app e `dmesg` do kernel, se permitido.
- Adicionar logging no próprio Mesa em cada fronteira: entrada do ICD, chamada a `drmGetDevices2`, abertura do render node, `drmGetVersion`, conexão SRV, handshake DDK, criação do dispositivo físico e retorno de `vkEnumeratePhysicalDevices`.
- Primeiro critério de sucesso: Mesa efetivamente selecionado e `vkEnumeratePhysicalDevices` retornando a BXM-8-256. Segundo: criar dispositivo lógico e executar probe de alocação, shader, submissão e swapchain. Só então comparar features com o Renut.
- O teste atual é Android 14/API 34. A versão do Android não muda a identidade física da GPU nem corrige incompatibilidade de ABI/bridge.

## Limite desta alteração

Este arquivo registra evidências e o plano de diagnóstico. Não altera código de bridge nem anuncia features Vulkan. A causa do crash Mesa precisa ser capturada antes de qualquer correção de backend: mudar IDs/versões ou marcar capabilities sem prova pode causar dano e não é validável com estes dois ZIPs.
