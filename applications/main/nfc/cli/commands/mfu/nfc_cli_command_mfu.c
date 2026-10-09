#include "nfc_cli_command_mfu.h"
#include "nfc_cli_action_info.h"
#include "nfc_cli_action_rdbl.h"
#include "nfc_cli_action_wrbl.h"

#define TAG "MFU"

//mfu info
const NfcCliActionDescriptor info_action = {
    .name = "info",
    .description = "Ziskat zakladni informace o karte",
    .alloc = nfc_cli_mfu_info_alloc_ctx,
    .free = nfc_cli_mfu_info_free_ctx,
    .execute = nfc_cli_mfu_info_execute,
    .key_count = 0,
    .keys = NULL,
};

const NfcCliKeyDescriptor rdbl_action_keys[] = {
    {
        .short_name = "b",
        .long_name = "block",
        .features = {.required = true, .parameter = true},
        .description = "pozadovane cislo bloku",
        .parse = nfc_cli_mfu_rdbl_parse_block,
    },
};

//mfu rdbl -b 0
//mfu rdbl --block 0
const NfcCliActionDescriptor rdbl_action = {
    .name = "rdbl",
    .description = "Precist blok z karty Ultralight",
    .alloc = nfc_cli_mfu_rdbl_alloc_ctx,
    .free = nfc_cli_mfu_rdbl_free_ctx,
    .execute = nfc_cli_mfu_rdbl_execute,
    .key_count = COUNT_OF(rdbl_action_keys),
    .keys = rdbl_action_keys,
};

const NfcCliKeyDescriptor wrbl_action_keys[] = {
    {
        .short_name = "b",
        .long_name = "block",
        .features = {.required = true, .parameter = true},
        .description = "pozadovane cislo bloku",
        .parse = nfc_cli_mfu_wrbl_parse_block,
    },
    {
        .short_name = "d",
        .long_name = "data",
        .features = {.required = true, .parameter = true},
        .description = "nova data bloku",
        .parse = nfc_cli_mfu_wrbl_parse_data,
    },
};

//mfu wrbl -b 0 -d DEADBEAF
//mfu rdbl --block 0 -- data DEADBEEF
const NfcCliActionDescriptor wrbl_action = {
    .name = "wrbl",
    .description = "Zapsat blok na kartu Ultralight",
    .alloc = nfc_cli_mfu_wrbl_alloc_ctx,
    .free = nfc_cli_mfu_wrbl_free_ctx,
    .execute = nfc_cli_mfu_wrbl_execute,
    .key_count = COUNT_OF(wrbl_action_keys),
    .keys = wrbl_action_keys,
};

const NfcCliActionDescriptor* mfu_actions[] = {
    &rdbl_action,
    &info_action,
    &wrbl_action,
};

//Command descriptor
ADD_NFC_CLI_COMMAND(mfu, "Prikazy specificke pro Mifare Ultralight", mfu_actions);
