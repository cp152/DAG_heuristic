// 在 n!=3*n_t 的情况下报错
// 将每三个点分为一组，每组点为 在一个通讯点的前后分别有一个计算点
// 对于每个 i<j ，第i组 和 第j组 间有独立的 p 概率存在一条边
// 每个点耗时在 [1,1000] 等概率随机
#include<bits/stdc++.h>
using namespace std;
int n,m,n_t;
double p;
auto seed = std::chrono::high_resolution_clock::now()
                .time_since_epoch()
                .count();
std::mt19937 rng(static_cast<unsigned>(seed));
pair<int,int> edge[10000007];
int main(int argc, char* argv[])
{
    if(argc < 5) {
        cerr << "Usage: " << argv[0] << " <n> <n_t> <p> <out_loc> [T]" << endl;
        return 1;
    }
    n = stoi(argv[1]);
    n_t = stoi(argv[2]);
    p = stod(argv[3]);
    string out_loc = argv[4];

    freopen(out_loc.c_str(), "w", stdout);
    if(n != n_t*3) {
        cerr << "Error: n must be equal to 3 * n_t." << endl;
        return 1;
    }

    for(int i=1;i<=n_t;i++){
        for(int j=i+1;j<=n_t;j++){
            if(rng()%1000<1000*p){
                edge[++m]={3*i,3*j-2};
                if(m > 10000000) {
                    cerr << "Error: Number of edges exceeds limit of 10^7." << endl;
                    return 1;
                }
            }
        }
    }
    for(int i=1;i<=n_t;i++){
        edge[++m]={3*i-2,3*i-1};
        edge[++m]={3*i-1,3*i};
    }

    cout<<n<<" "<<m<<"\n";

    for(int i = 1; i <= n_t; ++i) {
        cout << "c" << " " << rng() % 1000 + 1 << endl;
        cout << "t" << " " << rng() % 1000 + 1 << endl;
        cout << "c" << " " << rng() % 1000 + 1 << endl;
    }

    for(int i=1;i<=m;i++) cout<<edge[i].first<<" "<<edge[i].second<<"\n";
    return 0;
}