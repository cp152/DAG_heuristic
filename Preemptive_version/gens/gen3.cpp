// 在gen2的基础上，增加计算节点的期望时间消耗。希望能够提高“优先处理大的计算节点”的重要性。

// 结果：
// 考虑了“处理计算节点” 的 算法2/3/4 相较于 算法1 耗时有所降低，这个现象符合预期；但是难于判断这是否仅仅是因为计算节点占比变大后排序的重要性下降。
// // 补充：根据随机排列的结果来看，计算节点占比变大后，排序对于耗时的影响的比例确实大幅降低
// // 由此，代办：修改测试运行逻辑，同时计算一个随机排列的结果，比较时 取当前两个算法与随机排列的差值 进行比较。可以相对减少 “不同数据生成对于排序重要性的影响” ，更好地研究 “同一算法对于不同的图样式的效果差异”？？？？？
// 此外，各100次的运行中，仍然没有找到任何一个 算法1 劣于 算法2/3/4 的数据点，这点并不符合预期；
// 与随机排列的结果对比后发现，在当前数据生成的情况下 算法2 甚至劣于 随机排列 ！！！

// 分析：
// 对于算法2和算法3，可能是因为，没有对dag的全局的理解，而局部的信息作用有限，呈现出一种随机运行的情况。
// 对于算法4，这可能是由于该生成方式中，每个点后续的通信、计算节点数比值是固定的，又由大数定律，导致其通信计算节点耗时比值趋同。

// - 此外，这可能说明如果希望“最长尾链做法效果较差”数据生成器的“计算节点与通信节点耗时比值”需要有较为精确的分析与调整：
// - // 当 比值过小时，每个（非末尾段的）计算节点的时间区间内都容易有足够多的通信节点填充，此时为了减少末尾段的浪费，使用最长尾链的做法就很合理。
// - // 当 比值过大时，通信节点稀疏，……

// 在 n!=3*n_t 的情况下报错
// 将每三个点分为一组，每组点为 在一个通讯点的前后分别有一个计算点
// 对于每个 i<j ，第i组 和 第j组 间有独立的 p 概率存在一条边
// 通信节点耗时在 [1,1000] 等概率随机
// 计算节点耗时在 [1,100000] 等概率随机
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
        cout << "c" << " " << rng() % 100000 + 1 << endl;
        cout << "t" << " " << rng() % 1000 + 1 << endl;
        cout << "c" << " " << rng() % 100000 + 1 << endl;
    }

    for(int i=1;i<=m;i++) cout<<edge[i].first<<" "<<edge[i].second<<"\n";
    return 0;
}