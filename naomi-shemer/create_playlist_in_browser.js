// ============================================================================
// יצירת פלייליסט "שירי נעמי שמר - האוסף המקיף" (729 ביצועים) בחשבון היוטיוב שלך
// הוראות הפעלה:
// 1. פתח את https://www.youtube.com בדפדפן וודא שאתה מחובר לחשבון היוטיוב שלך.
// 2. לחץ Cmd+Option+J (במק) או F12 כדי לפתוח את ה-Console של הדפדפן.
// 3. הדבק את כל הקוד הזה ב-Console ולחץ Enter.
// תוך כ-10 שניות הפלייליסט ייווצר וייפתח אוטומטית!
// ============================================================================
(async function createNaomiShemerPlaylist() {
  const VIDEO_IDS = ["IUxt7faTExY", "H8V8yhc2eYI", "9xETAic8buQ", "hBlEx2bIRNI", "KaovY--ET14", "cpp8XENcuBk", "V4QSoLFj-NM", "mw9uiMMvFGk", "jk6lOLldgT4", "Xe4H1sCCAJo", "Zr-iKRNRzQk", "DEKLsquUP34", "TFIrOcriazY", "My9HiZIPsak", "zN2CRXhVJ3o", "bfQeAbF8-4A", "unyzPkoPBEs", "85QDrN6FB8Q", "dwUst6vBhs0", "ryXmue6dutA", "sFB_B3wTXLE", "-T6mxux7wKM", "4_Laz5PQV-Y", "tWs6g7hg0BI", "5Hz8UIWRADU", "BfKQ4bj0JJk", "gTXgnxD6Cuc", "1_dsV0afFgA", "JfJ3DrI7-6w", "NxoJzDVw4cc", "zpFGk2nz_-A", "-4bnvgAYqmo", "MFrjlagc8rE", "AvJZwh25uZ4", "M38vdprLLok", "07aL8h1LyJk", "418kExn65Ug", "ei2FcAMuRAw", "oNmwW4s3AuI", "0ypE8NBmyYo", "vrJcb0mauz8", "Zs1s0_fs9EI", "dDXngW-5jV0", "vQjWwS6X7CI", "6OWfRHNgEtg", "2iljNf6XqsA", "fE8xcZiFRO8", "whmUk6hiVE4", "I00dlNJc6BI", "-nzLbN3sFRQ", "5kl6qHnbp9Y", "BnKrb-46CNI", "kF5Lpl7IL6w", "zZHynZGet5g", "URL56lbFmr8", "e9lQpiSO6XM", "2QMxLPxD25g", "7uxKafYsUrU", "_NylGW8syfw", "BgpoI6q79Lw", "0IPY0etp8eE", "pWGF4nqxi9c", "AxnQ3qrsp64", "08Z_uYA9PLc", "XsDAsNDqHW4", "Ce_cSMB0Ri8", "5TZvR7wFlVo", "DdET9qVDfRI", "_DujVVkqqQ0", "neYlxPR8-WA", "ax7p4AggiqY", "zRQLXqjeRoE", "isxLekbAFHw", "4ZFF3v39RD4", "YQc4x6hGSyg", "q3XGUpCCTJs", "Q5N5gxqjDFc", "eCRBb3h6mz8", "9Er1RvAuM7M", "bzl8G_GQJKE", "7PxG0jfZX6k", "2aQJz8v_KkU", "XUR6jL3D6N8", "WFOhRFYM1wM", "QPPugl_l2ak", "mYfdJkb1gqg", "XKbvfLzHms4", "tk3zQs8gDTM", "4HZWNJzXTm4", "Okw-ktcRVr0", "UwhEUsWVdPg", "VCDKtBt4xb4", "jMlzihkguOU", "CeRvSDeJx-I", "8y5KQ8UWi0A", "2BfY0duzEpE", "7cZaZp3xfDM", "neNKCSaT1T8", "6hhQ_4omcKs", "Gi7-feW4FfE", "FkSHlF212BA", "aKAvYLWF97U", "GgYxh_MoCDA", "06dUzmJF7H0", "gkPyKqEFNSE", "MQOaZBQeo6U", "YY8vUjMWzEc", "Xoh_DVe4WcA", "ufIj60iGZqM", "sLvHms2BClA", "H3h-755AwoI", "0ga6HoypSJU", "DATGdPiFqVA", "ZcKAuoZSzWQ", "pKGFC7qoGBA", "D13BJwfsQu8", "l1b8s6ZGXhQ", "l8uDRKHspac", "dYYGjAoIU_E", "bZI8gT-VbT0", "ArRyqOnlQ3k", "_lds9E6qEQg", "z-OpnBf-JNI", "KOecGqpq-f0", "kF_MJiReEn0", "Y8ob5jdoYBw", "VkgQyNxNQqw", "qpbBemLcsUE", "aDZqwcq7eVI", "B0EO7nYCdu0", "SDCkIuEiWWY", "0XhvBFzatFc", "NWR0K-8lBhU", "MtwqXXIN6Xs", "5v77wNxd8Kw", "SgzeIwaaGMU", "T5o_o8lO-1M", "zV4aK_XyPW8", "wO3U1xG7Um0", "EFIwG44Egek", "P7eGfaq3E_s", "vVQ0Xmtb9_Q", "CYwiq1Uu5Ng", "pDLQ_FrzKL4", "i9bIVfz1HBw", "B7oZ2GPHhEU", "Ba1W41IDnhI", "ubenw8IJ9dE", "dZtHel6cUW8", "Brq81oCuNKc", "tz4ISVJyEfI", "-7qKw4AIGP4", "V8CR6u84pXU", "_aoBikUYiBY", "RJd_8iW_4AQ", "A6RoASKhCNU", "6EEIW68j5lY", "xAvvvAO6glU", "pCK483hwY-0", "vczM9eWy1yw", "jOpau37GjhY", "kRxN5b9yhKU", "z91zsr8vHnU", "erKzXsvfheA", "J1mbZ9eGho0", "2vq22hm-TnI", "_6La2mK-PqU", "PEamc15DDeY", "Pxm7UgJ1JiE", "cbNuUKAQMsU", "-eINxqt2z0A", "Ya2SuHzZAXo", "OfsdkuisiNo", "ZSYQh_YatoU", "acNmIrbrp0k", "XixXG6ffyy0", "GZW3RhiQeyY", "_LilpxfdvKc", "3H9EF4ZzVy8", "cD2GgbFD_Yo", "wFYq_Is8wJk", "HH2wou4FvsA", "R1tJE7-evoQ", "IXn5sqpAhqc", "DtlDXf6tveY", "Hv0SuDUsjyc", "QKmscJgKCYs", "3oB1QegwRqk", "6xpROKMcQus", "dgC-AI1O_a8", "-rGr-thBmjs", "Kc3Z01Zqr24", "jYVg9ERVMv0", "9XgKm2xg3iA", "3iQEC7mO3YY", "38jU5bVcNzo", "OBkMzEHYA3c", "LR_zCS48QV0", "1dAeJminXHM", "MhIbjL4Hghc", "YMdqSo7wMUk", "k8u50w4T-1g", "L8jFWAH86Hw", "sCQfgFoAQu4", "ldmMVGr-syE", "cITPhRNWoq0", "me0k188YXNw", "7e6hGajTOaE", "1uRrLed3pZc", "hSaod2F6TA8", "UxWCHV50LoU", "UeP8K2lXml8", "cV-WsBBOwto", "R-oz2dlpbvY", "C-rohkw6OX8", "EEq9IuWDBlM", "KSTaBxvL4JQ", "pUFhGuyD6j4", "LYoIOT8VvK0", "xdj8UWyGpFg", "CMhfrA5uDjE", "g-477LqGTr4", "SfPOduJnKvk", "OxafdSA-QkE", "0pdyuulvbzo", "OLQITmFP3Xo", "YMrwmCzH330", "3f8E0O3culE", "eGrPQv3g9ps", "Eff5K5VrmKE", "NhX0XzGmv9A", "0re6w_ZITxg", "wONNxGvP9S4", "vbG5B1wswQc", "kLf2ybtWLCI", "N4QGMJR3Qqo", "SOOmGDRVIK8", "q-9lO4eg7-w", "cAOakJcPmGs", "Y5aCrfJLjIM", "3YYVsJ9MGZQ", "xypLh9F1IXk", "VsVv0OOIARQ", "NXcXk-diyDY", "yWVoMYXeBpM", "w1hLRFc3jfo", "t_qzuM6V2Co", "Bac-K0Wjp2A", "rGRBY2iPjpk", "bnl-cjqYOwk", "E-jZMuDEvLQ", "Vimcno4QbUw", "E-G-dnLO99U", "cCftnvA1iJo", "KEOx2onVNDs", "Ur53Ai6WISA", "nOa7P6X2I-8", "e1c2MjdU9T8", "zUWmMkqQMQg", "t6jXzPCR0NA", "L7_tsGSLGTs", "OkWKy3URsDg", "VnReHM2MOuo", "Bujd3-vDfE8", "Ae_oPwsp_P0", "EikdgimAjd8", "ZKGMTf5XLCk", "8XCsox4ClH8", "AnWiRbrejHg", "p64TXGU2ipM", "qrvKQtQgb2s", "04AcSZS8K3s", "oNZG3NUzB3U", "gEacqh5DPk4", "DGUHUGnDYn0", "COoXTOZQYQ4", "7t6dTKHZY6U", "BAliJ1ieJrI", "r97YIa4BDnM", "A1BCQuWuvTE", "2GD7HJfapWM", "YWwJ1O6fQQs", "41VIMNNssjw", "hdskywcJSMo", "-dNwuLchpWg", "Im8ze1yI8Aw", "V2eI7l5c3nc", "m58C3mRgm5E", "ud8TFvfUJ8M", "hw_SJRb1uEk", "gkP9-OqJETY", "G5RVx22SVzs", "k0LjOdjBdYU", "oJZEOGPBtp0", "g_QXbJmWWO0", "9o-4qxrv584", "nOl7AAouxVc", "S9QL3kDf8gA", "ITgt-B5IdFk", "gRfvDuXwtYI", "VXLKQYTYShc", "O5In5PJnEr8", "aNWtipsXBEc", "gU6tE4TqExI", "LBTf6IMt2X8", "yXzElXsHH38", "ukOWgL-9mlw", "ZLzkd2ui6PM", "nNFb0CPT7Js", "doXUEtdMaxc", "tpe1wARxPSs", "Xw4qL0j_9Vs", "yKAUdNGyVpA", "61RF4uejHJE", "71Pqy6HKns8", "O4OhUorCxX8", "OFBBD-EuEfA", "6sR4GRdyZZ8", "Lg-Can0ZrXM", "g57hoYLobng", "tNga0kZsgXY", "yEG2trB0IxU", "-2f28ACy-Gk", "morcvF-aFsg", "piH6EOOP7cY", "xam-JFkXggk", "SzfqrHxbpug", "3a8B5imZV8o", "Rh-AfNJC1AY", "yzSOpEPUXWw", "CEI769yjg4g", "UgXcD55HXzc", "sdlmzqJiT5M", "pjCtGobuuSE", "BBUtEBZLJFQ", "2o1uo7sstSI", "RqHN-so83M4", "7ziQJmP02M0", "zuYjR6RNeIw", "mxCqvGI5iu0", "X3GCh50sW8A", "hZirnyIx1Tw", "VeeEHBwsyQw", "Ti6nFst0JaE", "P35Ek5tTy4I", "DLilbBb5C-k", "sdqrr4rdUPA", "0yT4idCIsSE", "qiWE67WQSBY", "1D4_GtYfmUE", "gfYmkBTQVD4", "s0923q2OCPM", "jzNc8KFQ4S4", "l4y16i5NwwQ", "L1QLv-RFy7A", "dGSCRDVe9NE", "wk0pllJl1nU", "E3V70DpK_EI", "X0EHaEth0TQ", "WDQyD0VHt68", "C-ZXUfY8c4U", "DZCXER0nGaM", "chw7OpsTH1A", "ydCddPTqZmo", "Z-JxFdJcoB4", "KXjJoVHJsQw", "6BfneC2-IvA", "tBL2uGdMMZ4", "2smvtZlQSEg", "V_AZsXtgxvY", "4gYlHwrMV50", "Yd63Irvr-Q0", "mzrn0p-yRSM", "dsZYpHVPjv0", "0XHUVfPJlak", "QYW7YCydh3s", "sKkBNzdlFvE", "24JJpjDS8QY", "cmQ9upI0aG8", "Jl0WahK00lU", "tnNhOpq6MqI", "sJFfiL_Y1_E", "hZwuhnWXkLE", "p3PIKVi8goc", "UOD51gynvJQ", "OzrUXu1pKkg", "o9ElrJy3fmk", "lfB0Y5mJ1qk", "UsNNGSI6qzk", "d8h9EDhbixA", "ORPN8djCQws", "bzLl7TH_VxQ", "9aIw7qJAOA4", "sgMLsWRX7SI", "VaztQIe75Ns", "KO7lZhbeFDs", "JAh-XgpCIEo", "X-KSBs_Lsd8", "PXL8ltjFDCk", "gpo_GVko6OA", "nz7sT486EYw", "ut3moC4G-QI", "omNa4PW1lU8", "ZYTJPE70ifA", "OdbpJIdes4Q", "WBfuFYdOQT4", "UfIj78lym1I", "_FhoSjLL61A", "EZ2zDG6qrJE", "8d9khSRpSkk", "qgyoXwMKJXg", "oQLUlVqXkpo", "mZxh2vHIBcs", "F6syH8W0EGA", "kO9D3crjEsU", "3v9rvDklaxc", "yavA7DK-_Lg", "JH-1IrNb_P4", "sFbghpqy0Lo", "wcy425HOqro", "tPX2FmmeM6k", "NGtt4OBuh2E", "reYLaGMYJYk", "JvQBz3CHrK0", "-p0EvZ_T_AY", "Luu_LIPtx-M", "OvN5nJ9bn2Y", "YtWovd6r0yc", "WxdVdudBKeE", "0Yn3EvME2ko", "WILLlFVs8K4", "VhBycovusXA", "AoGcmpu5D4Y", "nvaUD-WzYDQ", "iz3Et-1Ywe8", "XWOGYjtgJG0", "IWaGaO6VD4c", "2MUXbKJVRZo", "K1DBCpPxqeM", "T3qo2SYP52U", "OdYRuoXrHHw", "qvBk0IVkKRE", "fCi5ISYIy1U", "aG2s9Sp7tKg", "W6i7v9rr12o", "ciO3saZTmVs", "3-9PdBSxyvg", "Od9NL9RLW7M", "QUF8MiDp4O4", "oxzR9Z-kG6Q", "dWp4KgvyPYw", "ayYtqUQCYas", "g-7DSRZYyaY", "PL0HmLqbxpw", "VbIHsjgvE2g", "WBc7IWmf3cs", "dV91YmIuHV4", "Mf7VagPUG50", "_GD1f91Erg8", "E452vwyyVjQ", "_eq2jnCdcyA", "-Db1ucwfr1o", "erGG9tlYbBk", "z8JrHEVGykA", "oJS0DogSjXU", "A-6m6CKOdC4", "mypB2220Rfk", "sFfgH0oJdwE", "XHdb6YDvHII", "7T8wbdYlAbQ", "gRclcNmJ9fQ", "_nDa2esEWJk", "HgMGNLc5ir8", "AuYOGchQ6XI", "J41YP1kDIKw", "_8tfe7MY_uU", "ZJC7xzkrJwk", "7yMw3vG4_kU", "XtoKkNpyn-E", "BLpTR9p0mkY", "aO1sboxdmno", "dC2fS3vZAPY", "7kj9X6BnPKE", "FZp12hlp4gk", "HvE1Ib25iDk", "6hTkFqKThes", "fiU_B2M84Ww", "cRAhfb9Ypw8", "L-qU-BInVno", "e4cc_kptHk8", "vQPSLn2e4FY", "w2E3hxhbAc4", "EoHoiD_n7t4", "iPj5rmj8GZQ", "EdfxwaHVnAk", "-P0Gnvk5Kmk", "HlUl3uS6T6Q", "WK3WmcATcd0", "q4zRVBV0010", "Ue8yK2cnLTA", "He8KKInGwAE", "PkF2Y0bbbCo", "Jg42GYm1qv0", "eSmhtnivpvY", "HTMwVk8pQiY", "WZMQaNRyllY", "jd4eLSSa1Xs", "Xc6coB1-EPw", "06SSkPFTjfM", "Ar_Ua0MBt_w", "eUam8viOqxs", "jAnSY8gxLRg", "-vWfGW7Hf2E", "sCRw6hfgQTM", "AcZZ7fqUNTc", "bbIXevkZDnk", "WfM--seOsaY", "yscdF17IT_Y", "Pef5mRmx0fA", "kkJPYVGy31o", "_F3EdZ51O-Q", "Uwi4o3fwQwc", "1dDug8M2AYs", "wly5oxW3C6Y", "L7SIZBSQ6DM", "Picy0oa0wl0", "jfy9Pml8UZg", "vXAxaeNqze4", "0viBWDlQ9KE", "dLDcWMN-Fbw", "kA1Gl5w3ydI", "jfvSQpek00g", "ziATm-51Zc0", "FBMgpQRmfmo", "J8vmTovE2x0", "3iaTDb1K41o", "5VQkcCM1fmc", "OEVLRDRUxyc", "0u--FHf-LHU", "ms-YfEQM9E8", "SnARDknXrZQ", "3CdoBLw1V9w", "Sn0vSoeVXpI", "dKHjdN2hr4w", "vLhN2olc06o", "9NbtBvkX2TI", "aHVLk_SWyd0", "QeX9yVM_izg", "zEG-AcszgpQ", "TQwpuggfQWw", "6qiFa7eU34M", "_Yz2RSzE7c8", "f18phGNSyBg", "O9CoiUnwJ5A", "WA8fVawaHuw", "n6qfNKmjutM", "5yDnz_UrH-s", "5xj4ycn0TY8", "dFgoc8M87Ww", "jvZPz3tpWPw", "1gUgA5_iv5g", "sVEvT4pZeyQ", "JDThzHJWt4o", "vIF2MqBbbfk", "yT6IAbFTErU", "8hKBFliAjqQ", "0mcp9JqqJ1k", "ymL0Whh7V_I", "99iIWvXtsqc", "8UcwA-Zk3JQ", "GoWmzpyfv0Y", "uqOoO342wNg", "xkGxvP-tw1w", "qEYW8pnCu48", "3oHvXK3Xj5k", "p_OfoN-B_xw", "upipvN8Xw-c", "8327s02-Wzg", "cYZArmDfKnA", "s1SR4hmgC4U", "HBZpHQRKrFM", "g6clciS1riA", "H9uNgJUABMg", "gXM9-IpEzEc", "MuQ745D-jaE", "nruQWhRsem4", "7m9YwTJwFrE", "pTlgYtrDSPI", "3st5EgoczRM", "TmFdkd0YmjU", "s1Ac_TvGdAU", "ZFFJR9iTSuo", "ry9RV0yCJpI", "VYXKlyjOyyM", "TGRVtcThDf4", "p320GUpKgkQ", "hA92uD-XpQs", "lxr0_Ey9-vM", "OS9uUlfBrbA", "YgYyQjI4UeY", "C1PjhOZQxMU", "_Fxy_CFR78Q", "SiN-Wkyvj4w", "narkCrS3_GA", "lKhxVjkSa84", "XWnWPkDHGz4", "PrntU87z0n8", "R-bu_zssUEk", "wzrVRxyd5a4", "3G8xlTapGQo", "0rZlNPF_utQ", "vUmuxcvyGrM", "-2N-WzrLzCc", "sQTl_NH1n0o", "0krT8xzNbyM", "FZrRqLdaH5E", "XBrUmJLCkEw", "YrJtArqXavk", "TsA3LycTPSo", "PHQFSQi4tzU", "9bfiWAv4HSU", "YS6EfEQu1ik", "hDqbO57hnyQ", "EfcKLvzIDRw", "KvBOUWSO1PM", "Okj7fK4VSOA", "GyiSOeKOK8s", "DJFWTrj5sO8", "AIvWs1y1jLc", "Sah0hB6rSFY", "rLucwp89lnE", "4g6cymurqY0", "gq5PAlFBEi8", "_qb0WUb7i5A", "-1__PIJhhPI", "WhoJgSteCmI", "XeD27Barwbk", "dfPBgVKT_H8", "6yrG087cato", "Jzkgm9A3Ooc", "INHBTa-HfSM", "4ApYhj2Mqeo", "F25xFwezdxw", "PIqHAidM99g", "mtuSxIIZPqg", "qblckfTw1Rk", "5-8BIb9KyNk", "XOJchlUhps0", "_JG62QmM-QE", "evAV9e6QUlI", "uITVQ8JRMg4", "c0WSmr4tlLY", "0eWljspYG7E", "F7KHn6M2VGk", "ZMAdkTaAhqw", "_33ng3euFJI", "6rlo1KZ0qok", "F-tHf-vPBxQ", "sgVtXugsDtE", "jqQTqr1gHEI", "ExOobxzS4tc", "d9pbNfB26wc", "s6Geto53AmI", "RoUjcDIWqwc", "T9Q-EXevnts", "EEkIbuhQ9dw", "lXCnVOsgJwo", "CJ8_MISsRxg", "nNMmAneQsLs", "FFtI8ZQT2Mk", "B86J0eynF9A", "UB35E3hE65E", "CLDelMZYKC8", "xyiYZRhJsSo", "YfFNug5ZOac", "A9erliXTS6o", "x0IPLHoV9Yc", "JAY_uZjqmIA", "BncSM_l0_P8", "XIs2ZIJ2oZw", "mMEXXehlL54", "-xNyTz_yvRU", "gsf0t-VihvE", "4MJ1vA3znA4", "vxQcorAdAXA", "chuU4lFZ5iA", "pPE_eIQYtgY", "Yd3_uDW6i4w", "URuGgQXkQpQ", "vNw21mQVfKM", "agChJ2Ho124", "ycWudyVJdOU", "XteReGQom40", "W6iBl_lvP1s", "xI2m7tKJ40E", "vAT50nuKMh8", "i9KzXu-Nhx0", "Omn_wSe-dKU", "JUiRv74kgHU", "weX6vsG96ZY", "mpPxqJrum-M", "dT5g0VRp7jE", "n2t3bDiJcMk", "_vJ6UtXHybA", "U3xSpmrTgXc", "CSjnGcglVJI", "3wNpnpA5K-w", "2LRsVjehz44", "losUGtP6fxI", "skYeVk80Eo0", "cXln3eAat5g", "Pk0mm0ly7Og", "SZhwVVZuRkY", "CwORk-NwrQM", "H9f2NJOxcz0", "B7rC1GyPlqM", "YJKhOidPJhc", "Yk82zpkqZjw", "oo8IRR00H30", "k0RE3k8k1pQ", "mnXZeefSK8w", "nMxKk66pAzc", "6Z2BOKloo7k", "SdrmUgN92O4", "lmTSkGSnxzw", "9d8hI1wc_Bs", "fs14OduKHd4", "YYVengVA5V8", "oMZHElIjza4"];
  const PLAYLIST_TITLE = "שירי נעמי שמר";
  const PLAYLIST_DESC = "אוסף מקיף של שירי נעמי שמר (אלבומיה של נעמי שמר, ביצועים מקוריים מתוך אלבומים, הקלטות ארכיון וקאברים נבחרים). נוצר מתוך איחוד 9 מאגרים (אקו\"ם, הספרייה הלאומית, שירונט, ויקיפדיה, סטריאו ומונו, פזמונט, זמרשת, Discogs ו-MusicBrainz).";

  if (!window.ytcfg || typeof window.ytcfg.get !== "function") {
    alert("שגיאה: יש להריץ את הסקריפט מתוך לשונית פתוחה של https://www.youtube.com");
    return;
  }

  function getCookie(name) {
    const m = document.cookie.match(new RegExp("(?:^|; )" + name.replace(/([.$?*|{}()\[\]\\/+^])/g, "\\$1") + "=([^;]*)"));
    return m ? decodeURIComponent(m[1]) : null;
  }

  const sapisid = getCookie("SAPISID") || getCookie("__Secure-3PAPISID");
  if (!sapisid) {
    alert("שגיאה: לא נמצא חיבור לחשבון יוטיוב. אנא התחבר לחשבון היוטיוב שלך ב-https://www.youtube.com ונסה שוב.");
    return;
  }

  async function makeSapisidHash(origin) {
    const ts = Math.floor(Date.now() / 1000);
    const input = ts + " " + sapisid + " " + origin;
    const buf = await crypto.subtle.digest("SHA-1", new TextEncoder().encode(input));
    const hex = Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("");
    return "SAPISIDHASH " + ts + "_" + hex;
  }

  async function ytPost(endpoint, bodyObj) {
    const origin = window.location.origin;
    const auth = await makeSapisidHash(origin);
    const headers = {
      "Content-Type": "application/json",
      "Authorization": auth,
      "X-Origin": origin,
      "X-Goog-AuthUser": String(window.ytcfg.get("SESSION_INDEX") ?? "0"),
    };
    const visitor = window.ytcfg.get("VISITOR_DATA");
    if (visitor) headers["X-Goog-Visitor-Id"] = visitor;

    const resp = await fetch(origin + endpoint + "?prettyPrint=false", {
      method: "POST",
      credentials: "same-origin",
      headers,
      body: JSON.stringify({
        context: window.ytcfg.get("INNERTUBE_CONTEXT"),
        ...bodyObj
      })
    });
    if (!resp.ok) {
      const txt = await resp.text();
      throw new Error("HTTP " + resp.status + ": " + txt.slice(0, 300));
    }
    return resp.json();
  }

  console.log("🚀 יוצר פלייליסט חדש ביוטיוב:", PLAYLIST_TITLE);
  const createRes = await ytPost("/youtubei/v1/playlist/create", {
    title: PLAYLIST_TITLE,
    description: PLAYLIST_DESC,
    privacyStatus: "UNLISTED"
  });

  const playlistId = createRes.playlistId;
  if (!playlistId) {
    console.error("תגובת שרת:", createRes);
    throw new Error("לא התקבל playlistId מיוטיוב.");
  }
  console.log("✅ הפלייליסט נוצר בהצלחה! מזהה:", playlistId);

  const BATCH_SIZE = 50;
  for (let i = 0; i < VIDEO_IDS.length; i += BATCH_SIZE) {
    const batch = VIDEO_IDS.slice(i, i + BATCH_SIZE);
    console.log(`⏳ מוסיף שירים ${i + 1} עד ${Math.min(i + BATCH_SIZE, VIDEO_IDS.length)} מתוך ${VIDEO_IDS.length}...`);
    await ytPost("/youtubei/v1/browse/edit_playlist", {
      playlistId: playlistId,
      actions: batch.map(vid => ({
        action: "ACTION_ADD_VIDEO",
        addedVideoId: vid
      }))
    });
    await new Promise(r => setTimeout(r, 600));
  }

  const url = "https://www.youtube.com/playlist?list=" + playlistId;
  console.log("🎉 סיימנו! כל " + VIDEO_IDS.length + " השירים נוספו לפלייליסט:");
  console.log(url);
  window.open(url, "_blank");
})();
