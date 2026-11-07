# Diagnóstico DMC4/Mesa — enumeração PowerVR — 2026-11-06

## Evidência do aparelho

O log `dmc4-log-moto_g73_5G.txt` registra que o ModKit carregou `libvulkan_powervr_mesa.so` e que `vkCreateInstance` retornou `0` (`VK_SUCCESS`). Em seguida, o renderer do jogo informou `renderer init failed: no Vulkan device`. A captura não contém a contagem retornada por `vkEnumeratePhysicalDevices`, os campos de `VkPhysicalDeviceProperties` nem o resultado de `vkCreateDevice`; portanto, ainda não identifica se o ICD expôs um dispositivo que o jogo recusou.

## Código instrumentado

A patch 0007 adiciona logs temporários, prefixados por `PVR_DIAG`, sem mudar critérios de seleção, capabilities, extensões ou propriedades anunciadas. A instrumentação registra:

- resultado e quantidade de dispositivos retornados por `drmGetDevices2`, tipo de barramento e nós disponíveis;
- caminho do render node, resultado de abertura, nome/versão DRM e compatibilidade com PVR;
- resultado da inicialização do módulo Services e da conexão de bridge DDK;
- BVNC recebido do kernel e confirmação de presença na tabela Mesa;
- resultado da criação do winsys e do dispositivo físico;
- `deviceName`, `vendorID`, `deviceID`, `apiVersion`, `driverName`, `driverInfo` e BVNC calculados antes da publicação;
- confirmação de que o Mesa publicou o dispositivo físico na lista Vulkan.

A série de sete patches foi reaplicada com sucesso ao commit Mesa `0d94b3f397fb9cf8470bb5600ada8af79ff5361a`, o mesmo fixado pelo workflow. Isso valida aplicação e ordem dos patches, mas ainda não substitui o build Android do Actions nem um teste no telefone.

## Como interpretar a próxima captura

Se `drmGetDevices2` reportar zero dispositivos, o bloqueio está na descoberta de dispositivos DRM. Se houver candidatos, mas nenhum nó PVR compatível, o bloqueio aparece na disponibilidade do nó, acesso ou identificação DRM. Se o handshake falhar, os logs apontarão a etapa DDK. Se o BVNC for aceito e surgirem `exposed properties` e `published one PowerVR physical device`, o Mesa construiu e publicou uma GPU; a investigação passa então à enumeração/filtragem do DMC4. Se a inicialização física falhar, `VkResult` e os erros das etapas anteriores indicam onde.

Os registros usam `mesa_logw` para aparecer sem depender de propriedades `vendor.mesa.*`, que estavam inacessíveis no log anterior. Não foi executado nenhum probe de `ioctl` separado no dispositivo.
