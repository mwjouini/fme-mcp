def test_encoding() -> bool:
    geo_fmx = r"C:\Program Files\FME\transformers\GeographicBufferer.fmx"
    with open(geo_fmx, encoding="utf-8", errors="ignore") as fp:
        for line in fp:
            if "FACTORY_DEF * PythonFactory" in line:
                sc_idx = line.find("SOURCE_CODE ")
                out_idx = line.find("OUTPUT ", sc_idx)
                sc = line[sc_idx + len("SOURCE_CODE ") : out_idx].strip()
                replacements = [
                    ("<space>", " "),
                    ("<lf>", "\n"),
                    ("<openparen>", "("),
                    ("<closeparen>", ")"),
                    ("<apos>", "'"),
                    ("<comma>", ","),
                    ("<openbracket>", "["),
                    ("<closebracket>", "]"),
                    ("<opencurly>", "{"),
                    ("<closecurly>", "}"),
                    ("<quote>", '"'),
                    ("<backslash>", "\\"),
                ]
                decoded = sc
                for k, v in replacements:
                    decoded = decoded.replace(k, v)
                print("Decoded sample:")
                print(decoded[:150])
                compile(decoded, "<test>", "exec")
                print("Successfully compiled decoded GeographicBufferer python!")
                return True
    return False


if __name__ == "__main__":
    test_encoding()
