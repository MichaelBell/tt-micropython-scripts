RPOS_UF2FILE=RPI_PICO-20240222-v1.22.2.uf2

rm -rf build
mkdir build
pushd build
wget -O rp2-pico.uf2 https://micropython.org/resources/firmware/$RPOS_UF2FILE
mkdir upython_fs

pushd upython_fs
cp ../../*.py .
mv pmod_test.py main.py
popd

python -m uf2utils.examples.custom_pico --fs_root upython_fs --upython rp2-pico.uf2 --out test_qspi.uf2

pushd upython_fs
sed -i 's/qspi_test.TEST_RAM_B = True/qspi_test.TEST_RAM_B = False/' main.py
popd

python -m uf2utils.examples.custom_pico --fs_root upython_fs --upython rp2-pico.uf2 --out test_audio.uf2
