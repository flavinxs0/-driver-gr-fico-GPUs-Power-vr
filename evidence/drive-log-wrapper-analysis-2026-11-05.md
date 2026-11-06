# Análise do ZIP compartilhado no Google Drive — 2026-11-05

## Identificação

Arquivo baixado pelo ID do Drive `1_-VVYrK8RhdMna2g9YJeHnWnBbow71TQ`:

- Nome observado: `wrapper-powervr-arm64 (1).zip`
- Tamanho: 6.440.032 bytes
- SHA-256: `1da73002f18a4256a48a661c8e7497d0768b74d77716c5c264f2808c8f952627`
- Conteúdo externo:
  - `libvulkan_wrapper.so` — ELF AArch64, 10.742.960 bytes
  - `wrapper.tzst` — tar Zstandard, 2.710.318 bytes

O ZIP do Drive não é idêntico ao ZIP do `Download.zip`: o arquivo do Drive possui `wrapper.tzst` e o pacote local possuía `libc++_shared.so` junto do wrapper.

## Conteúdo do `wrapper.tzst`

```text
usr/share/vulkan/icd.d/wrapper_icd.aarch64.json
usr/lib/libadrenotools.so
usr/lib/libmain_hook.so
usr/lib/libhook_impl.so
usr/lib/libgsl_alloc_hook.so
usr/lib/libfile_redirect_hook.so
usr/lib/libvulkan_wrapper.so
```

Manifest ICD:

```json
{
  "ICD": {
    "api_version": "1.3.289",
    "library_path": "libvulkan_wrapper.so"
  },
  "file_format_version": "1.0.0"
}
```

## Descoberta principal

Este pacote é uma camada de integração Adrenotools/hook. Ele **não contém `libvulkan_powervr_mesa.so`**, nem `libvulkan_pvr_mesa.so`, nem outro ELF claramente identificável como o driver Mesa PVR nativo.

O pacote contém:

- `libvulkan_wrapper.so`: wrapper/interceptor Vulkan;
- `libadrenotools.so`: carregador de driver customizado;
- `libhook_impl.so`: hook de `android_dlopen_ext`;
- `libfile_redirect_hook.so`: redirecionamento de arquivos;
- `libgsl_alloc_hook.so`: hook de alocação GSL;
- `libmain_hook.so`: entrada do hook;
- manifest ICD que aponta para o wrapper.

Portanto, instalar apenas esse ZIP não instala o Mesa PVR. Ele precisa receber um driver customizado separado, pelo mecanismo Adrenotools, e o processo precisa conseguir localizar esse driver no diretório configurado.

## Dependências e risco de carregamento

`libvulkan_wrapper.so` depende de:

```text
libadrenotools.so
libcutils.so
liblog.so
libnativewindow.so
libsync.so
libz.so
libm.so
libxcb.so
libX11-xcb.so
libxcb-dri3.so
libxcb-present.so
libxcb-sync.so
libxcb-randr.so
libxcb-shm.so
libdrm.so
libc++_shared.so
libdl.so
libc.so
```

`libadrenotools.so`, `libhook_impl.so`, `libmain_hook.so`, `libgsl_alloc_hook.so` e `libfile_redirect_hook.so` usam RUNPATH:

```text
/data/data/com.termux/files/usr/lib
```

Isso é um caminho específico de Termux. Em um app Android normal, ele não existe necessariamente. O fato de o hook aparecer no log indica que parte dessas bibliotecas foi encontrada por outro caminho, mas a distribuição precisa garantir explicitamente `libc++_shared.so` e as bibliotecas auxiliares no namespace do processo.

## Relação com o log do Moto G56

O log mostrou que o hook conseguiu carregar:

```text
.../driver/libvulkan_powervr_mesa.so
```

Isso confirma que o mecanismo de driver customizado foi acionado. Contudo, o ZIP do Drive não fornece esse arquivo. Ele fornece somente o carregador/wrapper. Assim, há duas camadas que precisam ser distinguidas:

1. **Wrapper/loader:** o conteúdo deste ZIP;
2. **Driver Mesa PVR nativo:** `libvulkan_powervr_mesa.so`, que deve ser compilado e colocado no diretório de driver customizado.

O erro “o driver não tem dispositivo” ocorre na segunda camada ou na interface dela com o Android/DRM, não porque o manifest ICD esteja apontando diretamente para o Mesa nativo.

## O que aproveitar

### Aproveitar

- `libhook_impl.so` e `libfile_redirect_hook.so` como referência de carregamento e redirecionamento;
- `libadrenotools.so` e o manifest ICD como mecanismo de integração;
- `libmain_hook.so` e `libgsl_alloc_hook.so` somente se o app realmente precisar desses hooks;
- o manifest ICD, ajustando o nome e a localização da biblioteca final.

### Não tratar como Mesa PVR

- `libvulkan_wrapper.so` não substitui `libvulkan_powervr_mesa.so`;
- o wrapper não implementa o backend `pvrsrvkm` do Mesa;
- o manifest `wrapper_icd.aarch64.json` não comprova enumeração de um dispositivo PowerVR;
- as dependências XCB/DRM do wrapper não provam que o processo Android tem acesso ao render node.

## Próximo teste recomendado

Montar um pacote de teste explícito com:

```text
libvulkan_powervr_mesa.so       # Mesa nativo compilado
libvulkan_wrapper.so            # wrapper do Drive, se necessário
libadrenotools.so
libhook_impl.so
libmain_hook.so
libfile_redirect_hook.so
libgsl_alloc_hook.so
libc++_shared.so
```

Depois adicionar no Mesa logs de:

```text
drmGetDevices2()
open(/dev/dri/renderD*)
drmGetVersion()
pvr_srv_connection_create()
pvr_srv_init_module()
vkEnumeratePhysicalDevices()
```

O critério de sucesso é o retorno de pelo menos um `VkPhysicalDevice` BXM-8-256. O pacote do Drive, sozinho, não consegue atingir esse critério porque não contém o driver Mesa nativo.
